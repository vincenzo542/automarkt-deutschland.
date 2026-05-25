import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "automarkt.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            mileage INTEGER NOT NULL,
            fuel_type TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT,
            contact_email TEXT NOT NULL,
            created_at TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM cars")
    if c.fetchone()[0] == 0:
        sample_cars = [
            ("Volkswagen", "Golf GTI", 2021, 28500, 45000, "Essence", "Munich", "Très bon état, premier propriétaire.", "vendeur1@email.de", "2026-05-25"),
            ("BMW", "320i", 2020, 31000, 62000, "Essence", "Stuttgart", "Pack M, entretien complet chez BMW.", "vendeur2@email.de", "2026-05-25"),
            ("Audi", "A4 Avant", 2019, 24900, 89000, "Diesel", "Berlin", "Idéal famille, Grand coffre, Boîte auto.", "vendeur3@email.de", "2026-05-24"),
            ("Mercedes-Benz", "C220d", 2022, 39500, 32000, "Diesel", "Francfort", "Toit ouvrant, Caméra 360.", "vendeur4@email.de", "2026-05-23"),
        ]
        c.executemany("""
            INSERT INTO cars (brand, model, year, price, mileage, fuel_type, city, description, contact_email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_cars)
        conn.commit()
    conn.close()


def get_cars():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM cars ORDER BY id DESC", conn)
    conn.close()
    return df


def add_car(brand, model, year, price, mileage, fuel_type, city, description, email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        INSERT INTO cars (brand, model, year, price, mileage, fuel_type, city, description, contact_email, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (brand, model, year, price, mileage, fuel_type, city, description, email, date_now))
    conn.commit()
    conn.close()


def format_eur(value):
    return f"{int(value):,} €".replace(",", " ")


def format_km(value):
    return f"{int(value):,} km".replace(",", " ")


st.set_page_config(page_title="AutoMarkt Deutschland", page_icon="🚗", layout="wide")
init_db()

st.title("🚗 AutoMarkt Deutschland")
st.subheader("La plateforme d'achat et vente de voitures en Allemagne")

tab1, tab2 = st.tabs(["🔍 Acheter une voiture", "➕ Publier une annonce"])

with tab1:
    st.header("Trouvez votre future voiture")
    df_cars = get_cars()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        brands = ["Tous"] + sorted(df_cars["brand"].dropna().unique().tolist()) if not df_cars.empty else ["Tous"]
        selected_brand = st.selectbox("Marque", brands)

    with col2:
        max_price = st.slider("Prix Maximum (€)", min_value=0, max_value=100000, value=60000, step=1000)

    with col3:
        cities = ["Toutes"] + sorted(df_cars["city"].dropna().unique().tolist()) if not df_cars.empty else ["Toutes"]
        selected_city = st.selectbox("Ville / Région", cities)

    with col4:
        fuels = ["Tous"] + sorted(df_cars["fuel_type"].dropna().unique().tolist()) if not df_cars.empty else ["Tous"]
        selected_fuel = st.selectbox("Carburant", fuels)

    filtered_df = df_cars.copy()
    if not filtered_df.empty:
        if selected_brand != "Tous":
            filtered_df = filtered_df[filtered_df["brand"] == selected_brand]
        if selected_city != "Toutes":
            filtered_df = filtered_df[filtered_df["city"] == selected_city]
        if selected_fuel != "Tous":
            filtered_df = filtered_df[filtered_df["fuel_type"] == selected_fuel]
        filtered_df = filtered_df[filtered_df["price"] <= max_price]

    st.write(f"### {len(filtered_df)} annonce(s) disponible(s)")

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"### {row['brand']} {row['model']} ({row['year']})")
                c_a, c_b, c_c, c_d = st.columns(4)
                c_a.metric("Prix", format_eur(row["price"]))
                c_b.metric("Kilométrage", format_km(row["mileage"]))
                c_c.metric("Carburant", row["fuel_type"])
                c_d.metric("Localisation", row["city"])
                st.write(f"**Description :** {row['description']}")
                st.caption(
                    f"Publié le : {row['created_at']} | Contact vendeur : "
                    f"[{row['contact_email']}](mailto:{row['contact_email']})"
                )
                st.markdown("---")
    else:
        st.info("Aucune voiture ne correspond à vos critères de recherche.")

with tab2:
    st.header("Mettre en vente un véhicule")

    with st.form("add_car_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)

        with f_col1:
            brand = st.text_input("Marque *", placeholder="Ex: Audi")
            model = st.text_input("Modèle *", placeholder="Ex: A3")
            year = st.number_input("Année d'immatriculation *", min_value=1900, max_value=2026, value=2020)
            price = st.number_input("Prix (€) *", min_value=0, value=15000, step=500)

        with f_col2:
            mileage = st.number_input("Kilométrage (km) *", min_value=0, value=50000, step=1000)
            fuel_type = st.selectbox("Type de Carburant *", ["Essence", "Diesel", "Électrique", "Hybride"])
            city = st.text_input("Ville en Allemagne *", placeholder="Ex: Berlin")
            email = st.text_input("Votre adresse Email de contact *", placeholder="vendeur@example.de")

        description = st.text_area("Description du véhicule", placeholder="Détails sur l'état, les options...")
        submit_btn = st.form_submit_button("Publier mon annonce")

        if submit_btn:
            if not brand or not model or not city or not email:
                st.error("Veuillez remplir tous les champs obligatoires (*).")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Veuillez entrer une adresse email valide.")
            else:
                add_car(brand, model, year, price, mileage, fuel_type, city, description, email)
                st.success("Votre annonce a été publiée avec succès ! Consultez l'onglet d'achat pour la voir.")
                st.rerun()
