import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64

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
# 2. GESTION DE LA BASE DE DONNÉES & IMAGES
# ==========================================
def init_db():
    """Initialise la base de données et la met à jour pour les images."""
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    # Création de la table de base
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
    
    # Mise à jour automatique de la base pour ajouter la colonne image si elle manque
    try:
        c.execute("ALTER TABLE vehicles ADD COLUMN image TEXT")
    except sqlite3.OperationalError:
        # La colonne existe déjà, on continue
        pass
        
    conn.commit()
    conn.close()

def add_vehicle(marque, modele, prix, kilometrage, carburant, localisation, image_b64):
    """Ajoute un véhicule avec sa photo."""
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    date_ajout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO vehicles (marque, modele, prix, kilometrage, carburant, localisation, date_ajout, image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (marque, modele, prix, kilometrage, carburant, localisation, date_ajout, image_b64))
    conn.commit()
    conn.close()

@st.cache_data(ttl=60)
def get_vehicles():
    """Récupère les véhicules."""
    conn = sqlite3.connect('automarkt_pro.db')
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 3. INTERFACE UTILISATEUR
# ==========================================
st.title("🚗 AutoMarkt Deutschland - Plateforme Pro")
st.markdown("La marketplace sécurisée pour l'achat et la vente de véhicules.")

menu = st.sidebar.radio("Navigation", ["🔍 Chercher un véhicule", "➕ Publier une annonce", "📊 Tableau de bord"])

# ------------------------------------------
# PAGE 1 : CHERCHER UN VÉHICULE
# ------------------------------------------
if menu == "🔍 Chercher un véhicule":
    st.header("Trouvez votre future voiture")
    df = get_vehicles()
    
    if not df.empty:
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
        
        mask = (df['prix'] <= prix_max)
        if filtre_marque != "Toutes": mask &= (df['marque'] == filtre_marque)
        if filtre_ville != "Toutes": mask &= (df['localisation'] == filtre_ville)
        if filtre_carburant != "Tous": mask &= (df['carburant'] == filtre_carburant)
        df_filtre = df[mask]
        
        st.subheader(f"{len(df_filtre)} annonce(s) trouvée(s)")
        
        # Affichage avec Photos
        for index, row in df_filtre.iterrows():
            with st.container():
                st.markdown(f"### {row['marque']} {row['modele']}")
                
                # Séparation de l'écran : Photo à gauche, Infos à droite
                img_col, info_col = st.columns([1, 2])
                
                with img_col:
                    if pd.notna(row['image']) and row['image']:
                        try:
                            # Décodage de l'image
                            img_bytes = base64.b64decode(row['image'])
                            st.image(img_bytes, use_container_width=True)
                        except:
                            st.info("Erreur de chargement de l'image")
                    else:
                        st.info("📸 Aucune photo fournie")
                        
                with info_col:
                    c1, c2 = st.columns(2)
                    c1.metric("Prix", f"{row['prix']:,.0f} €".replace(',', ' '))
                    c2.metric("Kilométrage", f"{row['kilometrage']:,} km".replace(',', ' '))
                    
                    c3, c4 = st.columns(2)
                    c3.metric("Carburant", row['carburant'])
                    c4.metric("Localisation", row['localisation'])
                    
                    st.caption(f"Ajouté le : {row['date_ajout']}")
                st.divider()
    else:
        st.info("Aucun véhicule n'est actuellement en vente.")

# ------------------------------------------
# PAGE 2 : PUBLIER UNE ANNONCE
# ------------------------------------------
elif menu == "➕ Publier une annonce":
    st.header("Mettre un véhicule en vente")
    
    with st.form("form_ajout_vehicule", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nouvelle_marque = st.selectbox("Marque", ["Mercedes-Benz", "BMW", "Audi", "Volkswagen", "Porsche", "Tesla", "Renault", "Peugeot"])
            nouveau_modele = st.text_input("Modèle (ex: C220d, Golf 8)")
            nouveau_prix = st.number_input("Prix (€)", min_value=500, max_value=500000, step=500)
            
        with col2:
            nouveau_km = st.number_input("Kilométrage", min_value=0, max_value=500000, step=1000)
            nouveau_carburant = st.selectbox("Carburant", ["Diesel", "Essence", "Électrique", "Hybride"])
            nouvelle_loc = st.selectbox("Localisation", ["Magdeburg", "Berlin", "Munich", "Francfort", "Hambourg"])
        
        # Nouveau champ pour l'upload de la photo
        photo_upload = st.file_uploader("📸 Ajouter une photo du véhicule (Optionnel)", type=['png', 'jpg', 'jpeg'])
            
        submit = st.form_submit_button("Publier l'annonce")
        
        if submit:
            if nouveau_modele.strip() == "":
                st.error("Veuillez renseigner le modèle du véhicule.")
            else:
                # Traitement de l'image en Base64
                image_b64 = None
                if photo_upload is not None:
                    # Lire le fichier et l'encoder
                    image_bytes = photo_upload.read()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                
                add_vehicle(nouvelle_marque, nouveau_modele, nouveau_prix, nouveau_km, nouveau_carburant, nouvelle_loc, image_b64)
                st.success(f"✅ L'annonce pour la {nouvelle_marque} {nouveau_modele} a été publiée avec succès !")
                st.cache_data.clear()

# ------------------------------------------
# PAGE 3 : TABLEAU DE BORD
# ------------------------------------------
elif menu == "📊 Tableau de bord":
    st.header("Indicateurs de Performance (KPIs)")
    df = get_vehicles()
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total des annonces", len(df))
        col2.metric("Prix moyen", f"{df['prix'].mean():,.0f} €".replace(',', ' '))
        col3.metric("Marque la plus listée", df['marque'].mode()[0])
        
        # On n'affiche pas la colonne image (qui contient du texte illisible) dans le tableau
        df_display = df.drop(columns=['id', 'image']) if 'image' in df.columns else df.drop(columns=['id'])
        st.subheader("Base de données complète")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Pas assez de données pour générer des statistiques.")
