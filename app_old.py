import streamlit as st
from supabase import create_client, Client
import json
from io import BytesIO

st.set_page_config(page_title="Sántaság Annotáció")

# --- Oldal navigáció ---
st.sidebar.title("Navigáció")
page = st.sidebar.radio("Oldalak", ["Supabase Konfiguráció", "Főoldal"])


# ---------------- Supabase konfiguráció ----------------
if page == "Supabase Konfiguráció":
    st.title("🔧 Supabase Konfiguráció")
    SUPABASE_URL = st.text_input("Supabase URL", "https://sxamusxpevlkmdvbuqua.supabase.co")
    SUPABASE_KEY = st.text_input("Supabase API Key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4YW11c3hwZXZsa21kdmJ1cXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MzA0NDEsImV4cCI6MjA3MzUwNjQ0MX0.E-XSEUmXXGyP3Zh8xdrQJzmrQC_4Tl4lBV0xSfrHErI", type="password")
    BUCKET_NAME = st.text_input("Képek bucket neve", "santasag_annotalas")
    ANNOT_BUCKET = st.text_input("Annotációk bucket neve", "annotations")

    if st.button("Mentés"):
        if not SUPABASE_URL or not SUPABASE_KEY or not BUCKET_NAME or not ANNOT_BUCKET:
            st.warning("Kérlek, töltsd ki az összes mezőt a mentéshez.")
        else:
            st.session_state["supabase_config"] = {
                "url": SUPABASE_URL,
                "key": SUPABASE_KEY,
                "bucket_name": BUCKET_NAME,
                "annotations_bucket_name": ANNOT_BUCKET
            }
            st.success("✅ Konfiguráció mentve!")

elif page == "Főoldal":
    # Ellenőrizze, hogy a konfiguráció elérhető-e
    if "supabase_config" not in st.session_state:
        st.warning("Először állítsd be a Supabase konfigurációt a bal oldali menüben.")
        st.stop()

    # --- Supabase kliens inicializálása ---
    config = st.session_state["supabase_config"]
    supabase = create_client(config["url"], config["key"])
    BUCKET_NAME = config["bucket_name"]
    ANNOT_BUCKET = config["annotations_bucket_name"]

    # ---------------- Bejelentkezés ----------------
    st.title("🩺 Sántaság Annotációs Felület")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        email = st.text_input("Email", "testuser@gmail.com")
        password = st.text_input("Jelszó", "123456", type="password")
        if st.button("Bejelentkezés"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = user
                st.session_state["email"] = user.user.email
                st.session_state["supabase_config"] = {
                    "url": config["url"],
                    "key": config["key"],
                    "bucket_name": BUCKET_NAME,
                    "annotations_bucket_name": ANNOT_BUCKET
                }
                st.success("Sikeres bejelentkezés!")
                st.rerun()
            except Exception as e:
                st.error(f"Hiba a bejelentkezéskor: {e}")
        st.stop()

    # ---------------- Képek listázása ----------------
    # Lekérjük a képeket a bucketből
    all_files = supabase.storage.from_(BUCKET_NAME).list()
    all_file_names = [f["name"] for f in all_files]

    # Lekérjük az annotációkat, hogy ne jelenjenek meg újra
    annot_files = supabase.storage.from_(ANNOT_BUCKET).list()
    # Kinyerjük az annotált fájlok nevét a .json kiterjesztés nélkül
    annotated_file_names_with_extension = [f["name"] for f in annot_files]
    annotated_file_names = [f.replace(".json", "") for f in annotated_file_names_with_extension]

    # Csak a még annotálatlan képek a megadott képek bucketjéből
    files_to_annotate = [f for f in all_file_names if f not in annotated_file_names]

    if not files_to_annotate:
        st.info("Minden kép már annotálva van!")
        st.stop()

    selected_image = st.selectbox("Válassz képet annotáláshoz:", files_to_annotate)

    # ---------------- Kép megjelenítése ----------------
    if selected_image:
        image_url = supabase.storage.from_(BUCKET_NAME).get_public_url(selected_image)
        st.image(image_url)

        # ---------------- Annotáció ----------------
        label = st.radio("Annotáció:", ["sánta", "nem sánta", "nem eldönthető", "súlypontáthelyezés", "O-lábú", "széttárt labú"])
        comment = st.text_area("Megjegyzés:")

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

        if st.button("💾 Mentés", use_container_width=True):
            if label:
                # JSON létrehozása és bytes-á konvertálása
                annotation = {
                    "file": selected_image,
                    "label": label,
                    "comment": comment,
                    "annotator": st.session_state.user.user.email # Hozzáadva a felhasználó email címe
                }
                json_bytes = json.dumps(annotation).encode("utf-8")

                try:
                    # Ha létezik a fájl, törlés (felülíráshoz)
                    supabase.storage.from_(ANNOT_BUCKET).remove([f"{selected_image}.json"])
                except:
                    pass  # Ha még nem létezik, ne dobjon hibát

                try:
                    # Feltöltés
                    supabase.storage.from_(ANNOT_BUCKET).upload(
                        path=f"{selected_image}.json",
                        file=json_bytes
                    )
                    st.success(f"Annotáció mentve: {selected_image}.json")
                except Exception as e:
                    st.error(f"Hiba történt a mentés során: {e}")

                # Automatikus váltás a következő képre
                # Frissítjük a files_to_annotate listát a sikeres mentés után
                all_files = supabase.storage.from_(BUCKET_NAME).list()
                all_file_names = [f["name"] for f in all_files]
                annot_files = supabase.storage.from_(ANNOT_BUCKET).list()
                annotated_file_names_with_extension = [f["name"] for f in annot_files]
                annotated_file_names = [f.replace(".json", "") for f in annotated_file_names_with_extension]
                files_to_annotate = [f for f in all_file_names if f not in annotated_file_names]

                if files_to_annotate:
                    current_index = files_to_annotate.index(selected_image) if selected_image in files_to_annotate else -1
                    if current_index != -1 and current_index + 1 < len(files_to_annotate):
                         st.session_state["selected_image"] = files_to_annotate[current_index + 1]
                    elif files_to_annotate: # Ha a végén járunk, vagy a kiválasztott kép már nincs a listában, de van még annotálandó kép
                         st.session_state["selected_image"] = files_to_annotate[0]
                    st.rerun()
                else:
                     st.info("Minden kép már annotálva van!")
                     st.session_state["selected_image"] = None # Töröljük a kiválasztott képet
                     st.rerun()


            else:
                st.warning("Válassz egy kategóriát a mentéshez!")

    # Progress bar
    # Kiszámoljuk a teljes képek számát a képek bucketjében
    total_images = len(all_file_names)

    # Kiszámoljuk az annotált képek számát, amelyek a képek bucketjében lévő képekhez tartoznak
    annotated_images_in_bucket = [f for f in annotated_file_names if f in all_file_names]
    num_annotated = len(annotated_images_in_bucket)


    if total_images > 0:
        progress = num_annotated / total_images
        st.progress(progress)
        st.write(f"Annotált képek: {num_annotated}/{total_images}")
    else:
        st.write("Nincsenek képek a megadott bucketben.")
