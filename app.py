"""
Lameness Annotation Application with MinIO Storage.

This Streamlit application allows users to annotate cow lameness images
stored in MinIO object storage. Images are retrieved from preprocessed/oakd_43
folder structure and annotations are saved to the lameness bucket.
"""
import os
import streamlit as st
from supabase import create_client, Client
import json
from io import BytesIO
from PIL import Image
from my_minio_utils import MinioClient, load_config_from_yaml

st.set_page_config(page_title="Sántaság Annotáció")

# --- Cache functions ---
@st.cache_data(ttl=60)
def get_all_images(_minio_client, bucket, folder):
    """Cache image list for 60 seconds."""
    return _minio_client.list_images_from_preprocessed(bucket, folder)

@st.cache_data(ttl=10)
def get_all_annotations(_minio_client, bucket, folder):
    """Cache annotations list for 10 seconds."""
    return _minio_client.list_annotations(bucket, folder)

def get_annotated_file_names(all_annotations, all_images):
    """Extract annotated file names from annotation list."""
    annotated_file_names_with_extension = [f for f in all_annotations if f.endswith('.json')]
    annotated_file_names = []
    for annot_file in annotated_file_names_with_extension:
        base_name = annot_file[:-5]
        for img in all_images:
            img_base = os.path.splitext(img)[0]
            if img_base == base_name:
                annotated_file_names.append(img)
                break
    return annotated_file_names

# --- Automatikus konfiguráció betöltése ---
if "config_loaded" not in st.session_state:
    default_config = load_config_from_yaml("dev_config.yaml")
    
    if default_config:
        # Supabase config
        SUPABASE_URL = "https://sxamusxpevlkmdvbuqua.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4YW11c3hwZXZsa21kdmJ1cXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MzA0NDEsImV4cCI6MjA3MzUwNjQ0MX0.E-XSEUmXXGyP3Zh8xdrQJzmrQC_4Tl4lBV0xSfrHErI"
        
        # MinIO config
        MINIO_IP = default_config.get("MINIO_IP", "")
        MINIO_PORT = default_config.get("MINIO_PORT", "")
        ACCESS_KEY = default_config.get("ACCESS_KEY", "")
        SECRET_KEY = default_config.get("SECRET_KEY", "")
        IMAGES_BUCKET = default_config.get("Minio_images_bucket", "")
        IMAGES_FOLDER = default_config.get("Minio_images_folder", "")
        ANNOT_BUCKET = default_config.get("Minio_annot_bucket", "")
        ANNOT_FOLDER = default_config.get("Minio_annot_folder", "")
        
        if all([MINIO_IP, MINIO_PORT, ACCESS_KEY, SECRET_KEY, IMAGES_BUCKET, ANNOT_BUCKET]):
            try:
                # Create MinIO client
                endpoint = f"{MINIO_IP}:{MINIO_PORT}"
                minio_client = MinioClient(
                    endpoint=endpoint,
                    access_key=ACCESS_KEY,
                    secret_key=SECRET_KEY,
                    secure=False
                )
                
                # Save configs to session state
                st.session_state["supabase_config"] = {
                    "url": SUPABASE_URL,
                    "key": SUPABASE_KEY
                }
                st.session_state["minio_config"] = {
                    "endpoint": endpoint,
                    "access_key": ACCESS_KEY,
                    "secret_key": SECRET_KEY,
                    "images_bucket": IMAGES_BUCKET,
                    "images_folder": IMAGES_FOLDER,
                    "annot_bucket": ANNOT_BUCKET,
                    "annot_folder": ANNOT_FOLDER
                }
                st.session_state["minio_client"] = minio_client
                st.session_state["config_loaded"] = True
            except Exception as e:
                st.error(f"Hiba a konfiguráció betöltése során: {e}")

# --- Oldal navigáció ---
st.sidebar.title("Navigáció")
page = st.sidebar.radio("Oldalak", [ "Főoldal"])


# ---------------- Konfiguráció ----------------
# if page == "Konfiguráció":
#     st.title("Konfiguráció")
    
#     # Supabase beállítások
#     st.subheader("Supabase Beállítások")
#     SUPABASE_URL = st.text_input("Supabase URL", "https://sxamusxpevlkmdvbuqua.supabase.co")
#     SUPABASE_KEY = st.text_input("Supabase API Key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4YW11c3hwZXZsa21kdmJ1cXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MzA0NDEsImV4cCI6MjA3MzUwNjQ0MX0.E-XSEUmXXGyP3Zh8xdrQJzmrQC_4Tl4lBV0xSfrHErI", type="password")
    
#     st.divider()
    
#     # MinIO beállítások
#     st.subheader("MinIO Beállítások")
#     # Load default values from dev_config.yaml if available
#     default_config = load_config_from_yaml("dev_config.yaml")
    
#     MINIO_IP = st.text_input(
#         "MinIO IP cím", 
#         value=default_config.get("MINIO_IP", "152.66.249.108")
#     )
#     MINIO_PORT = st.text_input(
#         "MinIO Port", 
#         value=default_config.get("MINIO_PORT", "9090")
#     )
#     ACCESS_KEY = st.text_input(
#         "Access Key", 
#         value=default_config.get("ACCESS_KEY", "clientuser")
#     )
#     SECRET_KEY = st.text_input(
#         "Secret Key", 
#         value=default_config.get("SECRET_KEY", ""),
#         type="password"
#     )
    
#     IMAGES_BUCKET = st.text_input(
#         "Képek bucket neve", 
#         value=default_config.get("Minio_images_bucket", "preprocessed")
#     )
#     IMAGES_FOLDER = st.text_input(
#         "Képek mappa neve", 
#         value=default_config.get("Minio_images_folder", "oakd_43")
#     )
    
#     ANNOT_BUCKET = st.text_input(
#         "Annotációk bucket neve", 
#         value=default_config.get("Minio_annot_bucket", "lameness")
#     )
#     ANNOT_FOLDER = st.text_input(
#         "Annotációk mappa neve", 
#         value=default_config.get("Minio_annot_folder", "oakd_43")
#     )

#     if st.button("Mentés és Kapcsolódás"):
#         if not all([SUPABASE_URL, SUPABASE_KEY, MINIO_IP, MINIO_PORT, ACCESS_KEY, SECRET_KEY, IMAGES_BUCKET, ANNOT_BUCKET]):
#             st.warning("Kérlek, töltsd ki az összes mezőt a mentéshez.")
#         else:
#             try:
#                 # Create MinIO client
#                 endpoint = f"{MINIO_IP}:{MINIO_PORT}"
#                 minio_client = MinioClient(
#                     endpoint=endpoint,
#                     access_key=ACCESS_KEY,
#                     secret_key=SECRET_KEY,
#                     secure=False
#                 )
                
#                 # Check if buckets exist
#                 images_bucket_exists = minio_client.check_bucket_exists(IMAGES_BUCKET)
#                 annot_bucket_exists = minio_client.check_bucket_exists(ANNOT_BUCKET)
                
#                 if not images_bucket_exists:
#                     st.error(f"A '{IMAGES_BUCKET}' bucket nem létezik!")
#                 elif not annot_bucket_exists:
#                     st.error(f"Az '{ANNOT_BUCKET}' bucket nem létezik!")
#                 else:
#                     st.session_state["supabase_config"] = {
#                         "url": SUPABASE_URL,
#                         "key": SUPABASE_KEY
#                     }
#                     st.session_state["minio_config"] = {
#                         "endpoint": endpoint,
#                         "access_key": ACCESS_KEY,
#                         "secret_key": SECRET_KEY,
#                         "images_bucket": IMAGES_BUCKET,
#                         "images_folder": IMAGES_FOLDER,
#                         "annot_bucket": ANNOT_BUCKET,
#                         "annot_folder": ANNOT_FOLDER
#                     }
#                     st.session_state["minio_client"] = minio_client
#                     st.success("Sikeres kapcsolódás a MinIO szerverhez!")
#                     st.info(f"Képek bucket: {IMAGES_BUCKET}/{IMAGES_FOLDER}")
#                     st.info(f"Annotációk bucket: {ANNOT_BUCKET}/{ANNOT_FOLDER}")
                    
#             except Exception as e:
#                 st.error(f"Hiba a kapcsolódás során: {e}")

if page == "Főoldal":
    # Ellenőrizze, hogy a konfiguráció elérhető-e
    if "supabase_config" not in st.session_state or "minio_config" not in st.session_state or "minio_client" not in st.session_state:
        st.warning("Először állítsd be a konfigurációt a bal oldali menüben.")
        st.stop()

    # --- Supabase és MinIO kliens inicializálása ---
    supabase_config = st.session_state["supabase_config"]
    supabase = create_client(supabase_config["url"], supabase_config["key"])
    
    minio_config = st.session_state["minio_config"]
    minio_client = st.session_state["minio_client"]
    
    IMAGES_BUCKET = minio_config["images_bucket"]
    IMAGES_FOLDER = minio_config["images_folder"]
    ANNOT_BUCKET = minio_config["annot_bucket"]
    ANNOT_FOLDER = minio_config["annot_folder"]

    # ---------------- Bejelentkezés ----------------
    st.title("Sántaság Annotációs Felület")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.subheader("Bejelentkezés")
        email = st.text_input("Email", "testuser@gmail.com")
        password = st.text_input("Jelszó", "123456", type="password")
        
        if st.button("Bejelentkezés"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = user
                st.session_state["email"] = user.user.email
                st.success(f"Sikeres bejelentkezés: {user.user.email}")
                st.rerun()
            except Exception as e:
                st.error(f"Hiba a bejelentkezéskor: {e}")
        st.stop()

    # ---------------- Képek listázása ----------------
    st.sidebar.info(f"Bejelentkezve: {st.session_state['email']}")
    
    # Lekérjük a képeket a MinIO bucketből (cached)
    all_images = get_all_images(minio_client, IMAGES_BUCKET, IMAGES_FOLDER)
    
    if not all_images:
        st.error(f"Nem találhatók képek a '{IMAGES_BUCKET}/{IMAGES_FOLDER}' mappában!")
        st.stop()

    # Lekérjük az annotációkat (cached)
    all_annotations = get_all_annotations(minio_client, ANNOT_BUCKET, ANNOT_FOLDER)
    
    # Kinyerjük az annotált fájlok nevét
    annotated_file_names = get_annotated_file_names(all_annotations, all_images)

    # Csak a még annotálatlan képek a megadott képek bucketjéből
    files_to_annotate = [f for f in all_images if f not in annotated_file_names]

    if not files_to_annotate:
        st.success("Minden kép már annotálva van!")
        st.balloons()
        st.stop()

    # Képválasztó
    st.subheader("Képek annotálása")
    
    # Display folder structure info
    if files_to_annotate:
        sample_path = files_to_annotate[0]
        st.info(f"Mappa struktúra: {IMAGES_BUCKET}/{sample_path}")
    
    selected_image = st.selectbox(
        f"Válassz képet annotáláshoz ({len(files_to_annotate)} kép hátra):", 
        files_to_annotate
    )

    # ---------------- Kép megjelenítése ----------------
    if selected_image:
        # Display image path info
        st.caption(f"Kép: {selected_image}")
        
        # Initialize rotation state for current image
        if "current_image" not in st.session_state or st.session_state.current_image != selected_image:
            st.session_state.current_image = selected_image
            st.session_state.rotation_angle = 90  # Automatikusan balra 90 fokkal forgatva
        
        # Retrieve image from MinIO
        with st.spinner("Kép betöltése..."):
            image_data = minio_client.get_image(IMAGES_BUCKET, selected_image)
        
        if image_data:
            try:
                image = Image.open(BytesIO(image_data))
                
                # Apply rotation if needed
                if st.session_state.rotation_angle != 0:
                    image = image.rotate(st.session_state.rotation_angle, expand=True)
                
                # Rotation controls
                col1, col2, col3 = st.columns([1, 2, 3])
                with col1:
                    if st.button("Balra 90°"):
                        st.session_state.rotation_angle = (st.session_state.rotation_angle + 90) % 360
                        st.rerun()
                with col2:
                    if st.button("Jobbra 90°"):
                        st.session_state.rotation_angle = (st.session_state.rotation_angle - 90) % 360
                        st.rerun()
                with col3:
                    if st.session_state.rotation_angle != 0:
                        st.info(f"Forgatás: {st.session_state.rotation_angle}°")
                
                st.image(image, use_container_width=True)
            except Exception as e:
                st.error(f"Hiba a kép megjelenítése során: {e}")
                st.stop()
        else:
            st.error("Nem sikerült betölteni a képet!")
            st.stop()

        # ---------------- Annotáció ----------------
        st.subheader("Annotáció")
        
        label = st.radio(
            "Válassz kategóriát:", 
            ["sánta", "nem sánta", "nem eldönthető", "súlypontáthelyezés", "O-lábú", "széttárt lábú", "nincs tehén a képen"]
        )
        comment = st.text_area("Megjegyzés (opcionális):")

        # Custom button styling
        st.markdown(
            """
            <style>
            div.stButton > button:first-child {
                background-color: green;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }
            div.stButton > button:first-child:hover {
                background-color: darkgreen;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        if st.button("Mentés", use_container_width=True):
            if label:
                # Create annotation JSON
                annotation = {
                    "file": selected_image,
                    "label": label,
                    "comment": comment,
                    "annotator": st.session_state["email"]
                }
                json_bytes = json.dumps(annotation, ensure_ascii=False, indent=2).encode("utf-8")

                # Upload annotation to MinIO
                # Annotation path mirrors the image path with .json extension
                # Remove the file extension .jpg from the selected image path, multiple  place are dots
                name_without_ext, ext = os.path.splitext(selected_image)
                annotation_path = f"{name_without_ext}.json"
                
                with st.spinner("Annotáció mentése..."):
                    success = minio_client.upload_annotation(
                        ANNOT_BUCKET,
                        annotation_path,
                        json_bytes
                    )
                
                if success:
                    st.success(f"Annotáció mentve: {annotation_path}")
                    
                    # Clear cache to refresh annotations
                    get_all_annotations.clear()
                    
                    # Automatikus váltás a következő képre
                    # Frissítjük a files_to_annotate listát a sikeres mentés után
                    all_annotations = get_all_annotations(minio_client, ANNOT_BUCKET, ANNOT_FOLDER)
                    annotated_file_names = get_annotated_file_names(all_annotations, all_images)
                    files_to_annotate = [f for f in all_images if f not in annotated_file_names]

                    if files_to_annotate:
                        current_index = files_to_annotate.index(selected_image) if selected_image in files_to_annotate else -1
                        if current_index != -1 and current_index + 1 < len(files_to_annotate):
                            st.session_state["selected_image"] = files_to_annotate[current_index + 1]
                        elif files_to_annotate:  # Ha a végén járunk, vagy a kiválasztott kép már nincs a listában, de van még annotálandó kép
                            st.session_state["selected_image"] = files_to_annotate[0]
                        st.rerun()
                    else:
                        st.info("Minden kép már annotálva van!")
                        st.session_state["selected_image"] = None
                        st.rerun()
                else:
                    st.error("Hiba történt a mentés során!")
            else:
                st.warning("Válassz egy kategóriát a mentéshez!")

    # ---------------- Progress bar ----------------
    st.divider()
    st.subheader("Haladás")
    
    total_images = len(all_images)
    num_annotated = len(annotated_file_names)

    if total_images > 0:
        progress = num_annotated / total_images
        st.progress(progress)
        st.write(f"**Annotált képek:** {num_annotated}/{total_images} ({progress*100:.1f}%)")
        st.write(f"**Hátralevő képek:** {len(files_to_annotate)}")
    else:
        st.write("Nincsenek képek a megadott bucketben.")
