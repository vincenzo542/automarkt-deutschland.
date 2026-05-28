import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai

# --- CONFIGURATION IA ---
# Remplace par ta vraie clé API
genai.configure(api_key="TA_CLE_API_ICI")
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="AutoMarkt Pro", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('automarkt_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles 
                 (id INTEGER PRIMARY KEY, marque TEXT, modele TEXT, prix REAL, localisation TEXT)''')
    conn.commit()
    conn.close()

def get_data_as_text():
    conn = sqlite3.connect('automarkt_pro.db')
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    conn.close()
    return df.to_string()

init_db()

# --- INTERFACE ---
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Aller à", ["🔍 Catalogue", "🤖 Assistant IA"])

if menu == "🔍 Catalogue":
    st.title("Catalogue Automobile")
    st.table(pd.read_sql_query("SELECT * FROM vehicles", sqlite3.connect('automarkt_pro.db')))

elif menu == "🤖 Assistant IA":
    st.title("🤖 Conseiller Expert AutoMarkt")
    
    # Initialisation chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Interaction
    if prompt := st.chat_input("Ex: Je cherche une voiture à moins de 20 000€ à Berlin..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Récupération des données du catalogue pour donner du contexte à l'IA
        catalogue = get_data_as_text()
        
        system_instruction = f"""Tu es un expert automobile chez AutoMarkt. 
        Voici le catalogue actuel : {catalogue}. 
        Réponds aux clients, conseille-les selon leur budget et localisation."""
        
        with st.chat_message("assistant"):
            chat = model.start_chat(history=[])
            response = chat.send_message(system_instruction + "\nClient: " + prompt)
            full_response = response.text
            st.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
