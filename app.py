import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
import re

# ==========================================
# 1. CONFIGURATION SYSTEME & SÉCURITÉ IA
# ==========================================
st.set_page_config(
    page_title="AutoMarkt International Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Récupération sécurisée de la clé API via les Secrets Streamlit
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
    # Utilisation de gemini-1.5-flash : ultra-rapide et optimisé pour le contexte
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("🔑 Clé API manquante. Ajoutez 'api_key' dans les Secrets de Streamlit Cloud.")
    model = None

# ==========================================
# 2. BASE DE DONNÉES STRUCTURÉE (SQLITE)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('automarkt_pro.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marque TEXT NOT EXISTS,
                modele TEXT,
                prix REAL,
                type_offre TEXT, -- 'Vente' ou 'Location'
                ville TEXT,
                pays TEXT, -- 'France', 'Allemagne', 'Suisse'
                kilometrage INTEGER,
                carburant TEXT
            )
        ''')
        
        # Auto-population de démonstration internationale si la base est neuve
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            sample_cars = [
                ('Mercedes-Benz', 'C220d', 32000, 'Vente', 'Magdeburg', 'Allemagne', 45000, 'Diesel'),
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

init_db()

# ==========================================
# 3. MOTEUR DE RECHERCHE SEMANTIQUE (CONTEXTE)
# ==========================================
def extraire_contexte_pertinent(query):
    """Analyse la requête utilisateur pour extraire uniquement les véhicules correspondants en SQL"""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    
    if df.empty:
        return "Le catalogue est actuellement vide."
    
    # Filtrage dynamique par mots-clés (Villes et Pays)
    mots = query.lower()
    filtres = []
    
    # Détection géographie
    for idx, row in df.iterrows():
        if row['ville'].lower() in mots or row['pays'].lower() in mots:
            filtres.append(row)
            
    # Détection budget max
    prix_trouves = [int(s) for s in re.findall(r'\b\d[\d\s]{2,}\b', query.replace(' ', ''))]
    if prix_trouves:
        budget_max = max(prix_trouves)
        df_budget = df[df['prix'] <= budget_max]
        if not df_budget.empty:
            for _, r in df_budget.iterrows():
                filtres.append(r)

    # Si aucun filtre précis n'est détecté, on passe le top 10 des offres globales
    if not filtres:
        df_sub = df.head(10)
    else:
        df_sub = pd.DataFrame(filtres).drop_duplicates()
        
    return df_sub.to_string(index=False)

# ==========================================
# 4. INTERFACE UTILISATEUR (STREAMLIT)
# ==========================================
st.sidebar.markdown("# 🌐 AutoMarkt Global")
menu = st.sidebar.radio("Navigation Haute Performance", ["🔍 Recherche Avancée", "🤖 Assistant IA RAG Pro"])

# --- PAGE 1 : CATALOGUE ---
if menu == "🔍 Recherche Avancée":
    st.title("🔍 Catalogue Multi-Marchés (FR • DE • CH)")
    
    with get_db_connection() as conn:
        df_complet = pd.read_sql_query("SELECT * FROM vehicles", conn)
        
    col1, col2, col3 = st.columns(3)
    with col1:
        f_pays = st.multiselect("Filtrer par Pays", options=df_complet['pays'].unique(), default=df_complet['pays'].unique())
    with col2:
        f_type = st.selectbox("Type de transaction", ["Tous", "Vente", "Location"])
    with col3:
        f_budget = st.slider("Budget Maximum (€/*CHF*)", min_value=0, max_value=100000, value=100000, step=500)
        
    # Application des filtres SQL
    query_back = df_complet[df_complet['pays'].isin(f_pays) & (df_complet['prix'] <= f_budget)]
    if f_type != "Tous":
        query_back = query_back[query_back['type_offre'] == f_type]
        
    st.dataframe(query_back, use_container_width=True)

# --- PAGE 2 : ASSISTANT IA PROPULSÉ ---
elif menu == "🤖 Assistant IA RAG Pro":
    st.title("🤖 Conseiller IA Automobile RAG-Engine")
    st.caption("Notre IA analyse instantanément les stocks de France, d'Allemagne et de Suisse pour trouver la meilleure option.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Rendu graphique de l'historique
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: J'ai un budget de 30 000€, je vis en Allemagne. Que me conseilles-tu ?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if model:
            # ÉTAPE CLÉ : Extraction chirurgicale des données utiles
            contexte_catalogue = extraire_contexte_pertinent(prompt)
            
            # Directives système strictes pour encadrer le LLM international
            system_prompt = f"""
            Tu es l'agent IA d'élite de la plateforme AutoMarkt. Ton but est de vendre et louer des véhicules.
            Tu gères les requêtes pour la France, l'Allemagne, et la Suisse.
            
            Voici les données filtrées extraites en temps réel de notre base de données SQLite :
            {contexte_catalogue}
            
            Règles strictes de réponse :
            1. Si le client spécifie une localisation (ex: ville ou pays), propose en priorité les véhicules disponibles dans cette zone ou calcule mentalement une alternative dans un rayon proche.
            2. Si une offre correspond à son budget, mets-la en valeur avec des arguments convaincants.
            3. Sois professionnel, courtois, et réponds dans la langue utilisée par le client (Français, Allemand ou Anglais).
            4. Si aucun véhicule ne correspond parfaitement, propose l'alternative la plus proche et invite-le à contacter un point de vente.
            """
            
            with st.chat_message("assistant"):
                try:
                    with st.spinner("L'IA analyse le catalogue et calcule les meilleures options..."):
                        # Exécution de l'appel Gemini 1.5 Flash ultra-rapide
                        response = model.generate_content(system_prompt + "\n\nClient: " + prompt)
                        output_text = response.text
                        st.markdown(output_text)
                        st.session_state.chat_history.append({"role": "assistant", "content": output_text})
                except Exception as e:
                    st.error(f"⚠️ Erreur de communication avec le moteur d'IA : {e}")
        else:
            st.warning("⚠️ Le module IA est désactivé tant que la clé 'api_key' n'est pas ajoutée dans vos Secrets Streamlit.")
