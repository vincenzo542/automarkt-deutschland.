import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
import re
from datetime import datetime

# ==========================================
# 1. CONFIGURATION SYSTEME & SÉCURITÉ IA
# ==========================================
st.set_page_config(
    page_title="AutoMarkt Pro | Plateforme Globale", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de l'IA
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# ==========================================
# 2. GESTION DE LA BASE DE DONNÉES (Sécurisée)
# ==========================================
DB_PATH = 'automarkt_pro.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marque TEXT,
                modele TEXT,
                prix REAL,
                type_offre TEXT, 
                ville TEXT,
                pays TEXT, 
                kilometrage INTEGER,
                carburant TEXT,
                date_ajout TEXT
            )
        ''')
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            today = datetime.now().strftime("%Y-%m-%d")
            sample_cars = [
                ('Mercedes-Benz', 'C220d', 39500, 'Vente', 'Magdeburg', 'Allemagne', 32000, 'Diesel', today),
                ('BMW', 'Série 3', 450, 'Location', 'Paris', 'France', 20000, 'Essence', today),
                ('Audi', 'A4', 28500, 'Vente', 'Genève', 'Suisse', 60000, 'Diesel', today),
                ('Volkswagen', 'Golf', 180, 'Location', 'Berlin', 'Allemagne', 15000, 'Électrique', today),
                ('Peugeot', '208', 14500, 'Vente', 'Lyon', 'France', 35000, 'Essence', today)
            ]
            conn.executemany('''
                INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant, date_ajout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_cars)
            conn.commit()

init_db()

# Mise en cache pour des performances optimales
@st.cache_data(ttl=60)
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM vehicles ORDER BY id DESC", conn)

# Fonction sécurisée pour ajouter un véhicule
def add_vehicle(marque, modele, prix, type_offre, ville, pays, kilometrage, carburant):
    with sqlite3.connect(DB_PATH) as conn:
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute('''
            INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant, date_ajout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant, today))
        conn.commit()
    st.cache_data.clear() # Force le rafraîchissement des données

# ==========================================
# 3. INTERFACE UTILISATEUR & NAVIGATION
# ==========================================
st.sidebar.markdown("## 🌐 AutoMarkt OS")
menu = st.sidebar.radio("Menu Principal", [
    "📊 Tableau de Bord & Recherche", 
    "🤖 Assistant IA Client", 
    "⚙️ Espace Administrateur"
])

df_complet = load_data()

# --- ONGLET 1 : RECHERCHE & MÉTRIQUES ---
if menu == "📊 Tableau de Bord & Recherche":
    st.title("📊 Inventaire & Recherche Multi-Marchés")
    
    # Métriques d'entreprise
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Véhicules en stock", len(df_complet))
    col_m2.metric("Valeur totale du stock", f"{df_complet[df_complet['type_offre']=='Vente']['prix'].sum():,.0f} €".replace(',', ' '))
    col_m3.metric("Pays couverts", df_complet['pays'].nunique())
    col_m4.metric("Offres de location", len(df_complet[df_complet['type_offre']=='Location']))
    
    st.markdown("---")
    
    # Filtres de recherche dynamiques
    st.subheader("🔍 Filtrer l'inventaire")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        f_pays = st.multiselect("Pays", options=df_complet['pays'].unique(), default=df_complet['pays'].unique())
    with col2:
        f_type = st.selectbox("Type", ["Tous", "Vente", "Location"])
    with col3:
        f_carb = st.selectbox("Carburant", ["Tous"] + list(df_complet['carburant'].unique()))
    with col4:
        f_budget = st.number_input("Budget Max (€)", min_value=0, value=100000, step=1000)
        
    # Application des filtres
    query_back = df_complet[
        (df_complet['pays'].isin(f_pays)) & 
        (df_complet['prix'] <= f_budget)
    ]
    if f_type != "Tous": query_back = query_back[query_back['type_offre'] == f_type]
    if f_carb != "Tous": query_back = query_back[query_back['carburant'] == f_carb]
        
    st.dataframe(query_back.drop(columns=['id']), use_container_width=True)

# --- ONGLET 2 : CHATBOT IA ---
elif menu == "🤖 Assistant IA Client":
    st.title("🤖 Conseiller IA AutoMarkt")
    st.caption("Posez vos questions en français, allemand ou anglais. L'IA analyse notre base en temps réel.")

    if not model:
        st.error("⚠️ Clé API non détectée. Veuillez configurer les secrets Streamlit.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: Je cherche une voiture diesel à moins de 40 000€ à Magdeburg."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Création du contexte pour l'IA
        contexte = df_complet.to_csv(index=False)
        system_prompt = f"""
        Tu es un expert automobile travaillant pour AutoMarkt. Ton objectif est de réaliser des ventes et des locations.
        Voici notre inventaire actuel au format CSV :
        {contexte}
        
        Réponds à la demande du client de manière professionnelle, persuasive et précise. Ne propose QUE les véhicules présents dans l'inventaire.
        Si la question est en allemand, réponds en allemand.
        """
        
        with st.chat_message("assistant"):
            with st.spinner("Recherche dans le réseau..."):
                try:
                    response = model.generate_content(system_prompt + "\n\nDemande client: " + prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Erreur de communication avec l'IA: {e}")

# --- ONGLET 3 : ADMINISTRATION ---
elif menu == "⚙️ Espace Administrateur":
    st.title("⚙️ Gestion du Catalogue")
    st.markdown("Ajoutez de nouveaux véhicules à la base de données sécurisée.")
    
    with st.form("form_ajout_vehicule", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n_marque = st.text_input("Marque", placeholder="Ex: Porsche")
            n_modele = st.text_input("Modèle", placeholder="Ex: Macan")
            n_prix = st.number_input("Prix (€)", min_value=0, step=100)
            n_km = st.number_input("Kilométrage", min_value=0, step=1000)
        with col2:
            n_type = st.selectbox("Type d'offre", ["Vente", "Location"])
            n_carburant = st.selectbox("Carburant", ["Essence", "Diesel", "Électrique", "Hybride"])
            n_ville = st.text_input("Ville", placeholder="Ex: Munich")
            n_pays = st.text_input("Pays", placeholder="Ex: Allemagne")
            
        submitted = st.form_submit_button("➕ Ajouter au catalogue", use_container_width=True)
        
        if submitted:
            if n_marque and n_modele and n_ville and n_pays:
                add_vehicle(n_marque, n_modele, n_prix, n_type, n_ville, n_pays, n_km, n_carburant)
                st.success(f"✅ Le véhicule {n_marque} {n_modele} a été ajouté avec succès à la base de données !")
            else:
                st.error("⚠️ Veuillez remplir tous les champs textuels obligatoires.")def get_db_connection():
    # MODIFICATION ICI : On passe à 'automarkt_v3.db' pour écraser le cache corrompu
    conn = sqlite3.connect('automarkt_v3.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marque TEXT,
                modele TEXT,
                prix REAL,
                type_offre TEXT, 
                ville TEXT,
                pays TEXT, 
                kilometrage INTEGER,
                carburant TEXT
            )
        ''')
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            sample_cars = [
                ('Mercedes-Benz', 'C220d', 39500, 'Vente', 'Magdeburg', 'Allemagne', 32000, 'Diesel'),
                ('BMW', 'Série 3', 450, 'Location', 'Paris', 'France', 20000, 'Essence'),
                ('Audi', 'A4', 28500, 'Vente', 'Genève', 'Suisse', 60000, 'Diesel'),
                ('Volkswagen', 'Golf', 180, 'Location', 'Berlin', 'Allemagne', 15000, 'Électrique'),
                ('Peugeot', '208', 14500, 'Vente', 'Lyon', 'France', 35000, 'Essence')
            ]
            conn.executemany('''
                INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_cars)
            conn.commit()
            
