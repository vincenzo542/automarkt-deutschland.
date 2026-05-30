import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURATION DE L'APPLICATION (Doit obligatoirement être tout en haut)
# ==============================================================================
st.set_page_config(
    page_title="AutoMarkt Deutschland",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. GESTION DE LA BASE DE DONNÉES (Sécurisée)
# ==============================================================================
DB_NAME = "automarkt_v4.db"  # Nouvelle version pour éviter tout conflit de cache

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Création de la table si elle n'existe pas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marque TEXT NOT NULL,
                modele TEXT NOT NULL,
                prix REAL NOT NULL,
                type_offre TEXT NOT NULL,
                ville TEXT NOT NULL,
                pays TEXT NOT NULL,
                kilometrage INTEGER NOT NULL,
                carburant TEXT NOT NULL
            )
        ''')
        
        # Insertion de données de démonstration si la table est vide
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            sample_cars = [
                ('Mercedes-Benz', 'C220d', 39500, 'Vente', 'Magdeburg', 'Allemagne', 32000, 'Diesel'),
                ('BMW', 'Série 3', 25000, 'Vente', 'Paris', 'France', 20000, 'Essence'),
                ('Audi', 'A4', 28500, 'Vente', 'Genève', 'Suisse', 60000, 'Diesel'),
                ('Volkswagen', 'Golf', 18000, 'Vente', 'Berlin', 'Allemagne', 15000, 'Électrique'),
                ('Peugeot', '208', 14500, 'Vente', 'Lyon', 'France', 35000, 'Essence')
            ]
            conn.executemany('''
                INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_cars)
            conn.commit()

# Initialisation au démarrage
init_db()

def load_data():
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT * FROM vehicles", conn)

# ==============================================================================
# 3. INTERFACE & NAVIGATION SIDEBAR
# ==============================================================================
st.sidebar.title("🚗 AutoMarkt Pro")
menu = st.sidebar.radio(
    "Navigation :",
    ["🚗 Acheter une voiture", "➕ Publier une annonce", "🤖 Assistant IA"]
)

# Chargement initial des données globales
df_vehicles = load_data()

# ==============================================================================
# VUE 1 : ACHETER UNE VOITURE (Catalogue avec Filtres Dynamiques)
# ==============================================================================
if menu == "🚗 Acheter une voiture":
    st.title("🚗 AutoMarkt Deutschland")
    st.subheader("La plateforme d'achat et de vente de voitures en Europe")
    
    # Zone de filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        marques_dispo = ["Tous"] + sorted(df_vehicles['marque'].unique().tolist())
        selected_marque = st.selectbox("Marque", marques_dispo)
    with col2:
        prix_max = st.slider("Prix maximum (€)", min_value=0, max_value=100000, value=60000, step=1000)
    with col3:
        villes_dispo = ["Toutes"] + sorted(df_vehicles['ville'].unique().tolist())
        selected_ville = st.selectbox("Ville / Région", villes_dispo)
        
    # Application des filtres sur le DataFrame
    df_filtered = df_vehicles.copy()
    if selected_marque != "Tous":
        df_filtered = df_filtered[df_filtered['marque'] == selected_marque]
    if selected_ville != "Toutes":
        df_filtered = df_filtered[df_filtered['ville'] == selected_ville]
    df_filtered = df_filtered[df_filtered['prix'] <= prix_max]
    
    st.write(f"### 📋 {len(df_filtered)} annonce(s) disponible(s)")
    
    # Affichage sous forme de fiches élégantes
    for _, row in df_filtered.iterrows():
        with st.container():
            st.markdown(f"### {row['marque']} - {row['modele']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Prix", f"{int(row['prix'])} €")
            c2.metric("Kilométrage", f"{row['kilometrage']:,} km".replace(',', ' '))
            c3.metric("Localisation", f"{row['ville']}, {row['pays']}")
            c4.metric("Énergie", row['carburant'])
            st.markdown("---")

# ==============================================================================
# VUE 2 : PUBLIER UNE ANNONCE (Formulaire d'ajout sécurisé)
# ==============================================================================
elif menu == "➕ Publier une annonce":
    st.title("➕ Publier une nouvelle annonce")
    st.write("Remplissez le formulaire ci-dessous pour ajouter immédiatement votre véhicule au catalogue.")
    
    with st.form("add_car_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            marque = st.text_input("Marque *").strip()
            modele = st.text_input("Modèle *").strip()
            prix = st.number_input("Prix (€) *", min_value=0, value=15000)
            type_offre = st.selectbox("Type d'offre", ["Vente", "Location"])
        with c2:
            ville = st.text_input("Ville *").strip()
            pays = st.text_input("Pays *", value="Allemagne").strip()
            kilometrage = st.number_input("Kilométrage (km) *", min_value=0, value=50000)
            carburant = st.selectbox("Carburant", ["Essence", "Diesel", "Électrique", "Hybride"])
            
        submit_button = st.form_submit_button("🚀 Publier l'annonce")
        
        if submit_button:
            if not marque or not modele or not ville:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires (*).")
            else:
                with get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant))
                    conn.commit()
                st.success(f"🎉 Succès ! Votre {marque} {modele} a bien été ajoutée au catalogue.")
                st.balloons()

# ==============================================================================
# VUE 3 : ASSISTANT IA (Propulsé par Google Gemini avec accès au Catalogue)
# ==============================================================================
elif menu == "🤖 Assistant IA":
    st.title("🤖 Assistant IA Intelligent")
    st.write("Posez vos questions à notre IA pour trouver le véhicule idéal (ex: *Je cherche un diesel à moins de 30000€*).")
    
    # 1. Vérification sécurisée de la clé API présente dans les Secrets Streamlit
    if "api_key" not in st.secrets:
        st.error("⚠️ Clé API manquante. Veuillez ajouter votre clé nommée `api_key` dans l'onglet **Secrets** des paramètres de Streamlit Cloud.")
    else:
        # Configuration de l'API Gemini
        genai.configure(api_key=st.secrets["api_key"])
        
        # Initialisation de l'historique des messages dans Streamlit
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Affichage des messages existants
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Traitement d'une nouvelle saisie utilisateur
        if prompt := st.chat_input("Ex: Je cherche une voiture à moins de 20 000€..."):
            # Afficher le message utilisateur
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            # Préparation du contexte catalogue pour l'IA
            contexte_catalogue = df_vehicles.to_string(index=False)
            
            # Message système pour guider l'IA sur son rôle et son stock réel
            system_instruction = f"""
            Tu es l'assistant commercial virtuel officiel de 'AutoMarkt Deutschland'. 
            Ton but est d'aider poliment l'utilisateur à trouver une voiture en fonction de sa demande.
            Voici l'état actuel en temps réel de notre catalogue de véhicules disponibles :
            {contexte_catalogue}
            
            Consignes importantes :
            1. Réponds toujours de manière professionnelle, chaleureuse et en français.
            2. Si l'utilisateur cherche une voiture présente dans la liste ci-dessus, propose-la lui en donnant ses détails (Prix, Kilométrage, Ville).
            3. Si aucun véhicule ne correspond exactement à son budget ou à sa ville, indique-le lui poliment et propose l'alternative la plus proche disponible dans la liste.
            """
            
            # Appel de l'IA (Modèle ultra-rapide Gemini 1.5 Flash)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # On assemble l'instruction système et l'historique pour l'envoi
                    full_prompt = f"{system_instruction}\n\nHistorique de la discussion:\n"
                    for m in st.session_state.messages[:-1]:
                        full_prompt += f"{m['role']}: {m['content']}\n"
                    full_prompt += f"user: {prompt}\nassistant:"
                    
                    response = model.generate_content(full_prompt)
                    ai_response = response.text
                    
                    # Affichage propre du résultat
                    message_placeholder.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    message_placeholder.error(f"Une erreur est survenue lors de la communication avec l'IA : {str(e)}")
import streamlit as st
import google.generativeai as genai

class AssistantCommercialIA:
    def __init__(self, api_key, catalogue_data=""):
        """
        Initialise l'agent IA avec une mémoire persistante et un contexte métier.
        """
        # Configuration sécurisée de la clé API
        genai.configure(api_key=api_key)
        
        # Le "Cerveau" de l'agent : Instructions système puissantes
        system_prompt = f"""
        Tu es l'assistant IA expert de notre marketplace automobile premium.
        Ton but est d'accompagner les clients pour trouver le véhicule parfait.
        
        Règles de comportement :
        1. Sois extrêmement courtois, professionnel et concis.
        2. Analyse le besoin du client (budget, type de trajet, famille).
        3. Ne propose QUE les véhicules présents dans notre catalogue actuel.
        
        [STOCK EN TEMPS RÉEL]
        {catalogue_data}
        """
        
        # Utilisation du modèle Flash pour des réponses quasi-instantanées
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        # Initialisation de la mémoire de conversation dans Streamlit
        if "chat_session" not in st.session_state:
            # start_chat() gère automatiquement l'historique des messages !
            st.session_state.chat_session = self.model.start_chat(history=[])

    def poser_question(self, message_utilisateur):
        """
        Envoie le message à l'IA et gère les erreurs potentielles pour ne pas faire crasher l'app.
        """
        try:
            reponse = st.session_state.chat_session.send_message(message_utilisateur)
            return reponse.text
        except Exception as e:
            return f"Oups, j'ai eu une petite coupure de réseau. L'erreur exacte est : {e}"

# ==========================================
# EXEMPLE D'UTILISATION DANS TON MENU STREAMLIT
# ==========================================
# 1. Tu récupères ton catalogue en texte (comme on l'a fait avant)
# contexte_catalogue = df_vehicles.to_string(index=False)

# 2. Tu initialises l'agent
# agent = AssistantCommercialIA(
#     api_key=st.secrets["api_key"], 
#     catalogue_data=contexte_catalogue
# )

# 3. Tu gères l'interface de chat
# if prompt := st.chat_input("Que cherchez-vous ?"):
#     # Afficher la question
#     st.chat_message("user").markdown(prompt)
#     
#     # Obtenir la réponse de l'IA
#     reponse_ia = agent.poser_question(prompt)
#     
#     # Afficher la réponse
#     st.chat_message("assistant").markdown(reponse_ia)
