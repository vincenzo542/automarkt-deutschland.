import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURATION DE L'APPLICATION
# ==========================================
st.set_page_config(
    page_title="AutoMarkt Deutschland",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. GESTION DE LA BASE DE DONNÉES (Sécurisée)
# ==========================================
def init_db():
    """Initialise la base de données SQLite."""
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    # Création de la table avec des types de données stricts
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marque TEXT NOT NULL,
            modele TEXT NOT NULL,
            prix REAL NOT NULL,
            kilometrage INTEGER NOT NULL,
            carburant TEXT NOT NULL,
            localisation TEXT NOT NULL,
            date_ajout TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_vehicle(marque, modele, prix, kilometrage, carburant, localisation):
    """Ajoute un véhicule avec des requêtes paramétrées (Protection Anti-Injection SQL)."""
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    date_ajout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # L'utilisation des '?' sécurise les entrées utilisateurs
    c.execute('''
        INSERT INTO vehicles (marque, modele, prix, kilometrage, carburant, localisation, date_ajout)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (marque, modele, prix, kilometrage, carburant, localisation, date_ajout))
    conn.commit()
    conn.close()

# Mise en cache pour accélérer le chargement des données
@st.cache_data(ttl=60)
def get_vehicles():
    """Récupère tous les véhicules sous forme de DataFrame Pandas."""
    conn = sqlite3.connect('automarkt_pro.db')
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    conn.close()
    return df

# Initialiser la DB au démarrage
init_db()

# ==========================================
# 3. INTERFACE UTILISATEUR (UI / UX)
# ==========================================
st.title("🚗 AutoMarkt Deutschland - Plateforme Pro")
st.markdown("La marketplace sécurisée pour l'achat et la vente de véhicules.")

# Barre de navigation latérale
st.sidebar.header("Navigation")
menu = st.sidebar.radio("Que souhaitez-vous faire ?", ["🔍 Chercher un véhicule", "➕ Publier une annonce", "📊 Tableau de bord"])

# ------------------------------------------
# PAGE 1 : CHERCHER UN VÉHICULE
# ------------------------------------------
if menu == "🔍 Chercher un véhicule":
    st.header("Trouvez votre future voiture")
    
    df = get_vehicles()
    
    if not df.empty:
        # Système de filtres en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            marques_dispos = ["Toutes"] + list(df['marque'].unique())
            filtre_marque = st.selectbox("Marque", marques_dispos)
        with col2:
            prix_max = st.slider("Prix Maximum (€)", min_value=1000, max_value=200000, value=100000, step=1000)
        with col3:
            villes_dispos = ["Toutes"] + list(df['localisation'].unique())
            filtre_ville = st.selectbox("Ville / Région", villes_dispos)
        with col4:
            carburants_dispos = ["Tous"] + list(df['carburant'].unique())
            filtre_carburant = st.selectbox("Carburant", carburants_dispos)
        
        # Application des filtres
        mask = (df['prix'] <= prix_max)
        if filtre_marque != "Toutes": mask &= (df['marque'] == filtre_marque)
        if filtre_ville != "Toutes": mask &= (df['localisation'] == filtre_ville)
        if filtre_carburant != "Tous": mask &= (df['carburant'] == filtre_carburant)
        
        df_filtre = df[mask]
        
        st.subheader(f"{len(df_filtre)} annonce(s) trouvée(s)")
        
        # Affichage professionnel des résultats
        for index, row in df_filtre.iterrows():
            with st.container():
                st.markdown(f"### {row['marque']} {row['modele']}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Prix", f"{row['prix']:,.0f} €".replace(',', ' '))
                c2.metric("Kilométrage", f"{row['kilometrage']:,} km".replace(',', ' '))
                c3.metric("Carburant", row['carburant'])
                c4.metric("Localisation", row['localisation'])
                st.caption(f"Ajouté le : {row['date_ajout']}")
                st.divider()
    else:
        st.info("Aucun véhicule n'est actuellement en vente. Soyez le premier à publier une annonce !")

# ------------------------------------------
# PAGE 2 : PUBLIER UNE ANNONCE
# ------------------------------------------
elif menu == "➕ Publier une annonce":
    st.header("Mettre un véhicule en vente")
    
    with st.form("form_ajout_vehicule", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nouvelle_marque = st.selectbox("Marque", ["Mercedes-Benz", "BMW", "Audi", "Volkswagen", "Porsche"])
            nouveau_modele = st.text_input("Modèle (ex: C220d, Golf 8)")
            nouveau_prix = st.number_input("Prix (€)", min_value=500, max_value=500000, step=500)
            
        with col2:
            nouveau_km = st.number_input("Kilométrage", min_value=0, max_value=500000, step=1000)
            nouveau_carburant = st.selectbox("Carburant", ["Diesel", "Essence", "Électrique", "Hybride"])
            nouvelle_loc = st.selectbox("Localisation", ["Magdeburg", "Berlin", "Munich", "Francfort", "Hambourg"])
            
        submit = st.form_submit_button("Publier l'annonce")
        
        if submit:
            if nouveau_modele.strip() == "":
                st.error("Veuillez renseigner le modèle du véhicule.")
            else:
                add_vehicle(nouvelle_marque, nouveau_modele, nouveau_prix, nouveau_km, nouveau_carburant, nouvelle_loc)
                st.success(f"✅ L'annonce pour la {nouvelle_marque} {nouveau_modele} a été publiée avec succès !")
                # Vider le cache pour afficher la nouvelle voiture immédiatement
                st.cache_data.clear()

# ------------------------------------------
# PAGE 3 : TABLEAU DE BORD (Analytics)
# ------------------------------------------
elif menu == "📊 Tableau de bord":
    st.header("Indicateurs de Performance (KPIs)")
    
    df = get_vehicles()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total des annonces", len(df))
        col2.metric("Prix moyen", f"{df['prix'].mean():,.0f} €".replace(',', ' '))
        col3.metric("Marque la plus listée", df['marque'].mode()[0])
        
        st.subheader("Base de données complète")
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("Pas assez de données pour générer des statistiques.")
