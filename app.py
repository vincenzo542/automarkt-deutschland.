import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="AutoMarkt Deutschland", page_icon="🚗", layout="wide")

# ==========================================
# 2. BASE DE DONNÉES
# ==========================================
def init_db():
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, marque TEXT, modele TEXT, prix REAL, kilometrage INTEGER, carburant TEXT, localisation TEXT, date_ajout TEXT, image TEXT)''')
    conn.commit()
    conn.close()

def get_vehicles():
    conn = sqlite3.connect('automarkt_pro.db')
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    conn.close()
    return df

def add_vehicle(marque, modele, prix, kilometrage, carburant, localisation, image_b64):
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    date_ajout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO vehicles (marque, modele, prix, kilometrage, carburant, localisation, date_ajout, image) VALUES (?,?,?,?,?,?,?,?)', (marque, modele, prix, kilometrage, carburant, localisation, date_ajout, image_b64))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. INTERFACE
# ==========================================
st.title("🚗 AutoMarkt Deutschland")
menu = st.sidebar.radio("Navigation", ["🔍 Chercher un véhicule", "➕ Publier une annonce", "🤖 Assistant IA", "📊 Tableau de bord"])

# --- PAGE CHERCHER ---
if menu == "🔍 Chercher un véhicule":
    df = get_vehicles()
    if not df.empty:
        st.write("Liste des véhicules...")
        st.dataframe(df)
    else:
        st.info("Aucun véhicule.")

# --- PAGE PUBLIER ---
elif menu == "➕ Publier une annonce":
    st.header("Publier")
    with st.form("ajout"):
        m = st.text_input("Marque")
        mo = st.text_input("Modèle")
        p = st.number_input("Prix")
        k = st.number_input("Km")
        c = st.selectbox("Carburant", ["Diesel", "Essence"])
        l = st.text_input("Localisation")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            add_vehicle(m, mo, p, k, c, l, None)
            st.success("Ajouté !")

# --- PAGE ASSISTANT ---
elif menu == "🤖 Assistant IA":
    st.header("🤖 Conseiller Automobile")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Quel budget ?"}]
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Votre question ?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Réponse basique
        reponse = "Je suis un assistant simple pour le moment."
        with st.chat_message("assistant"):
            st.markdown(reponse)
        st.session_state.messages.append({"role": "assistant", "content": reponse})

# --- PAGE TABLEAU ---
elif menu == "📊 Tableau de bord":
    st.header("Données")
    st.write(get_vehicles())
