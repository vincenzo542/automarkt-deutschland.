# ------------------------------------------
# PAGE 3 : ASSISTANT IA
# ------------------------------------------
elif menu == "🤖 Assistant IA":
    st.header("🤖 Conseiller Automobile IA")
    st.markdown("Posez vos questions sur notre catalogue, votre budget ou les locations à proximité.")

    # 1. Initialiser l'historique de la discussion
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour ! Je suis l'IA d'AutoMarkt. Quel est votre budget, et dans quelle ville cherchez-vous un véhicule ?"}
        ]

    # 2. Afficher les anciens messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Zone de texte pour l'utilisateur
    if prompt := st.chat_input("Ex: J'ai 15 000€ et je cherche une voiture près de Magdeburg..."):
        
        # Ajouter le message de l'utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 4. Logique de l'IA (Recherche dans la base de données)
        with st.chat_message("assistant"):
            df = get_vehicles()
            reponse_ia = ""
            
            # Analyse très basique des mots-clés (À remplacer plus tard par l'API OpenAI)
            mots_cles = prompt.lower()
            
            if df.empty:
                reponse_ia = "Notre catalogue est actuellement vide, revenez plus tard !"
            else:
                # Filtrage par ville dynamique selon ce que l'utilisateur tape
                villes_dispos = df['localisation'].str.lower().unique()
                ville_trouvee = None
                for v in villes_dispos:
                    if v in mots_cles:
                        ville_trouvee = v
                        break
                
                if ville_trouvee:
                    df_filtre = df[df['localisation'].str.lower() == ville_trouvee]
                    reponse_ia += f"📍 J'ai regardé nos points de vente près de **{ville_trouvee.capitalize()}**. "
                else:
                    df_filtre = df
                    reponse_ia += "🌍 Voici ce que je peux vous conseiller sur l'ensemble de notre réseau international. "

                # Simulation de recommandation par budget (ex: si l'utilisateur tape un nombre)
                import re
                nombres = re.findall(r'\d+', prompt.replace(' ', ''))
                if nombres:
                    budget = int(nombres[0])
                    if budget > 1000: # On assume que c'est un budget
                        df_budget = df_filtre[df_filtre['prix'] <= budget]
                        if not df_budget.empty:
                            vehicule_top = df_budget.iloc[0]
                            reponse_ia += f"Avec votre budget de {budget}€, je vous recommande vivement cette **{vehicule_top['marque']} {vehicule_top['modele']}** à {vehicule_top['prix']}€, disponible immédiatement en {vehicule_top['carburant']}."
                        else:
                            reponse_ia += f"Malheureusement, je n'ai pas de véhicules en dessous de {budget}€ dans cette zone pour le moment."
                else:
                    reponse_ia += "Précisez-moi votre budget pour que je puisse affiner ma recherche."
menu = st.sidebar.radio("Navigation", ["🔍 Chercher un véhicule", "➕ Publier une annonce", "🤖 Assistant IA", "📊 Tableau de bord"])
            # Afficher et sauvegarder la réponse
            st.markdown(reponse_ia)
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
