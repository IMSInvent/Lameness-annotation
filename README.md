# Lameness-annotation

Alkalmazás indítása: streamlit run app.py

Az alapértelmezett értékekkel is használható.

Szükséges Supabase beállítások:

*	Projekt Settings/Authentication/Users helyen user felvétele, email címmel és jelszóval

*	Képeket tartalmazó publikus storage

*	Annotálásokat tartalmazó publikus storage

*	Képeket tartalmazó storagehoz SELECT policy beállítása (Storage/Policies)

*	Annotálásokat tartalmazó storagehoz SELECT, INSERT policy beállítása

A fenti felületen meg kell adni a project URL-t (Project Settings/Data API), illetve a anon API kulcsot (Project Settings/API Keys), valamint a 2 bucket nevét. Ezután mentés és a bal oldali Navigációnál a kattints a Főoldalra.

Itt bekell jelentkezni a Supabase-ben beállított userrel és mehet is az annotálás. A mentésnél automatikusan vált, illetve eltűnik a kép a legördülő listából.
