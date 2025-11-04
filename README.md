# Lameness-annotation

Sántaság annotációs alkalmazás MinIO object storage használatával.

## Telepítés

```bash
pip install -r requirements.txt
```

## Alkalmazás indítása

```bash
streamlit run app_minio.py
```

## Konfiguráció

Az alkalmazás Supabase autentikációt és MinIO object storage-ot használ.

### Konfigurációs fájlok

- **dev_config.yaml**: Fejlesztői konfiguráció (alapértelmezett értékekkel)
- **config.yaml**: Sablon konfiguráció (üres értékekkel)

### MinIO beállítások

A konfigurációs fájlban a következő paramétereket kell megadni:

```yaml
# MinIO szerver kapcsolat
MINIO_IP = ""
MINIO_PORT = ""
ACCESS_KEY = ""
SECRET_KEY = ""

# Képek bucket (preprocessed/oakd_43/YYYY/MM/DD/ struktúra)
Minio_images_bucket = ""
Minio_images_folder = ""

# Annotációk bucket
Minio_annot_bucket = ""
Minio_annot_folder = ""
```

### Mappa struktúra

A képek a következő struktúrában vannak tárolva:
```
preprocessed/
  └── oakd_43/
      └── YYYY/
          └── MM/
              └── DD/
                  ├── image1.jpg
                  ├── image2.jpg
                  └── ...
```

Az annotációk ugyanilyen struktúrában kerülnek mentésre a `lameness` bucketbe, `.json` kiterjesztéssel.

## Használat

Az alkalmazás automatikusan betölti a konfigurációt a `dev_config.yaml` fájlból indításkor.

1. **Főoldal**:
   - Jelentkezz be Supabase email címmel és jelszóval
   - Válassz egy képet a listából
   - Szükség esetén forgasd el a képet a "Balra 90°" vagy "Jobbra 90°" gombokkal
   - Annotáld a képet a megfelelő kategóriával
   - Adj hozzá opcionális megjegyzést
   - Kattints a "Mentés" gombra
   - Az alkalmazás automatikusan a következő nem annotált képre vált


### Annotációs kategóriák

- sánta
- nem sánta
- nem eldönthető
- súlypontáthelyezés
- O-lábú
- széttárt lábú
- nincs rajta tehén

