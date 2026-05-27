import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE L'APPLICATION ---
st.set_page_config(page_title="AutoMarkt Deutschland", page_icon="🚗", layout="wide")

# --- GESTION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marque TEXT, modele TEXT, 
                  prix REAL, kilometrage INTEGER, carburant TEXT, localisation TEXT)''')
    conn.commit()
    conn.close()

def get_vehicles():
    conn = sqlite3.connect('automarkt_pro.db')
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    conn.close()
    return df

init_db()

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["🔍 Chercher un véhicule", "🤖 Assistant IA", "📊 Tableau de bord"])

# --- PAGE 1 : CHERCHER UN VÉHICULE ---
if menu == "🔍 Chercher un véhicule":
    st.header("🔍 Catalogue des véhicules")
    df = get_vehicles()
    if not df.empty:
        st.dataframe(df)
    else:
        st.write("Aucun véhicule disponible pour le moment.")

# --- PAGE 2 : ASSISTANT IA (CHATBOT) ---
elif menu == "🤖 Assistant IA":
    st.header("🤖 Conseiller Automobile IA")
    st.write("Je peux vous aider à choisir une voiture selon votre budget.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour ! Quel est votre budget pour votre futur véhicule ?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Je cherche une voiture à moins de 15000 euros"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logique simplifiée de l'IA
        df = get_vehicles()
        reponse = "Je n'ai pas trouvé de véhicule correspondant à vos critères."
        
        # Extraction de budget dans le texte
        import re
        nombres = re.findall(r'\d+', prompt.replace(' ', ''))
        
        if nombres:
            budget = int(nombres[0])
            vehicules_budget = df[df['prix'] <= budget]
            if not vehicules_budget.empty:
                meilleure = vehicules_budget.iloc[0]
                reponse = f"Pour votre budget de {budget}€, je vous suggère cette **{meilleure['marque']} {meilleure['modele']}** à {meilleure['prix']}€ localisée à {meilleure['localisation']}."
            else:
                reponse = f"Désolé, je n'ai rien trouvé sous les {budget}€."

        with st.chat_message("assistant"):
            st.markdown(reponse)
        st.session_state.messages.append({"role": "assistant", "content": reponse})

# --- PAGE 3 : TABLEAU DE BORD ---
elif menu == "📊 Tableau de bord":
    st.header("📊 Données brutes")
    st.write(get_vehicles())
