from components.gen_llm_response import generate_llm_response
from components.loadModel import generate_with_llama
import streamlit as st
def interface(model_fn, embedding_model, collection, api_collection):
 # Ajout du fond d'écran doux gris clair
    st.markdown(
        """
        <style>
            body, .stApp {
                background-color: #26272C;
            }
            .css-18e3th9 {
                background-color: #26272C;
            }
            button {
            background-color: #727383 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            transition: background-color 0.3s;
            }
            button:hover {
                background-color: #d4d4d4 !important;
                color: #26272C !important;
            }
            input, textarea, .stTextInput > div > div > input {
                background-color: #393A41 !important;
                border: 1px solid #cccccc !important;
                border-radius: 6px !important;
                padding: 0.5rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.title("🤖 Chatbot Mistral-7B GGUF avec mémoire RAG")
    st.write("Posez une question ou lancez un quizz d’orientation.")

    # ✅ Init historique et état du quizz
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "show_quizz" not in st.session_state:
        st.session_state.show_quizz = False

    if "quizz_step" not in st.session_state:
        st.session_state.quizz_step = 0

    if "quizz_answers" not in st.session_state:
        st.session_state.quizz_answers = {}
    # ✅ Message d'accueil affiché une seule fois
    if "welcome_shown" not in st.session_state:
        st.session_state.welcome_shown = True
        st.session_state.chat_history.append(("Chatbot", "Bonjour 👋 ! Je suis ton assistant d’orientation. Pose-moi une question ou clique sur *Faire le quizz d'orientation* pour commencer."))

    # ✅ Bouton pour lancer ou réinitialiser le quizz
    if st.button("🎓 Faire le quizz d'orientation"):
        st.session_state.show_quizz = True
        st.session_state.quizz_step = 0
        st.session_state.quizz_answers = {}

    # ✅ Déroulement du quizz
    questions = [
        ("interet", "Qu’est-ce qui t’intéresse le plus ?", ["Sciences", "Art", "Informatique", "Commerce", "Nature"]),
        ("competence", "Dans quoi es-tu le plus à l’aise ?", ["Communiquer", "Résoudre des problèmes", "Créer", "Organiser"]),
        ("travail", "Tu préfères travailler...", ["En équipe", "Seul", "En extérieur", "Avec les mains"]),
        ("etudes", "Jusqu’où veux-tu poursuivre tes études ?", ["Bac", "Bac+2", "Bac+5", "Doctorat"]),
        ("objectif", "Ton objectif principal ?", ["Gagner de l’argent", "Aider les autres", "Innover", "Être indépendant"])
    ]

    if st.session_state.show_quizz and st.session_state.quizz_step < len(questions):
        key, q_text, options = questions[st.session_state.quizz_step]
        st.subheader(f"🧠 Question {st.session_state.quizz_step + 1} sur {len(questions)}")
        choice = st.radio(q_text, options, key=key)
        if st.button("Suivant"):
            st.session_state.quizz_answers[key] = choice
            st.session_state.quizz_step += 1
            st.rerun()

    elif st.session_state.show_quizz and st.session_state.quizz_step >= len(questions):
        st.success("✅ Quizz terminé ! Voici tes réponses :")
        st.json(st.session_state.quizz_answers)

        # ✅ Suggestions uniquement si bouton cliqué
        if st.button("🔍 Voir suggestions de métiers", key="suggestions_btn"):
            prompt = f"Voici le profil d'un étudiant : {st.session_state.quizz_answers}. Quels métiers pourraient lui convenir ?"
            response = generate_llm_response(user_input, model_fn, embedding_model, collection, api_collection)
            st.session_state.chat_history.append(("Vous", prompt))
            st.session_state.chat_history.append(("Chatbot", response))
            st.rerun()

        # ✅ Revenir au chatbot
        if st.button("↩️ Revenir au chatbot", key="back_btn"):
            st.session_state.show_quizz = False
            st.session_state.quizz_step = 0
            st.session_state.quizz_answers = {}
            st.rerun()

    # ✅ Affichage du chatbot si pas en mode quizz

    if not st.session_state.show_quizz:
        for sender, message in st.session_state.chat_history:
            st.write(f"**{sender}** : {message}")

        with st.form(key="chat_form"):
            user_input = st.text_input("Posez votre question :", "")
            submitted = st.form_submit_button("Envoyer")

        if submitted and user_input:
            response = generate_llm_response(user_input, model_fn, embedding_model, collection, api_collection)
            st.session_state.chat_history.append(("Vous", user_input))
            st.session_state.chat_history.append(("Chatbot", response))
            st.rerun()