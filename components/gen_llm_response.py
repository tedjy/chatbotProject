from components.initialize import initialize
from components.recup_data import retrieve_api_data, retrieve_memory, trouver_diplome
from components.addToMemory import add_to_memory
from components.loadModel import load_model

# Initialisation
embedding_model, collection, api_collection = initialize()
model, tokenizer = load_model()


def has_age(text):
    return any(a in text.lower() for a in ["ans", "j'ai", "âge", "age", "an"])


def has_diplome(text):
    return any(d in text.lower() for d in ["bts", "bac", "cap", "licence", "master", "diplôme", "niveau"])


def has_ville(text):
    return any(v in text.lower() for v in ["paris", "lille", "marseille", "roubaix", "lyon", "nantes", "ville"])


def generate_llm_response(prompt, model, tokenizer, embedding_model, collection, api_collection):
    """ Génère une réponse intelligente et fluide pour un assistant d’orientation scolaire """

    # 🔁 Récupération mémoire + données
    memory = retrieve_memory(prompt, embedding_model, collection)
    api_data = retrieve_api_data(prompt, embedding_model, api_collection)

    # 🧠 Contexte conversationnel
    context_elements = []
    if memory:
        context_elements.append("🧠 Historique récent :\n" + "\n\n".join([str(m) for m in memory[-1:]]))
    context = "\n".join(context_elements)
    texte_global = f"{prompt} {context}".lower()

    # 🔍 Vérifie si des infos manquent
    questions = []
    if not has_age(texte_global):
        questions.append("Quel est ton âge ?")
    if not has_diplome(texte_global):
        questions.append("Quel est ton dernier diplôme obtenu ?")
    if not has_ville(texte_global):
        questions.append("Dans quelle ville vis-tu ?")

    if questions:
        response = "Pour mieux t’aider, j’ai besoin de quelques infos :\n" + "\n".join(f"- {q}" for q in questions)
        add_to_memory(prompt, response, embedding_model, collection)
        return response

    # 🧠 Dictionnaire des diplômes
    diplomes_reference = {}
    for item in api_data:
        formation = item.get("Formation", "").lower()
        domaine = item.get("Domaine", "inconnu")
        niveau = item.get("Niveau de sortie", "inconnu")

    if any(x in formation for x in ["bts", "bac pro", "cap", "licence", "master","bac"]):
        diplomes_reference[formation] = {
            "niveau": niveau,
            "domaine": domaine
        }
        print("diplomes references ",diplomes_reference)

    # 🎯 Matching du diplôme
    match_diplome, infos_diplome = trouver_diplome(prompt, diplomes_reference)
    if match_diplome:
        context_elements.append(
            f"🎓 Diplôme identifié : {match_diplome} ({infos_diplome['niveau']}, domaine : {infos_diplome['domaine']})"
        )

        # 🔍 Filtrage sémantique du domaine
        domaine_oriente = infos_diplome["domaine"]
        vector = embedding_model.encode(domaine_oriente).tolist()

        results = api_collection.query(
            query_embeddings=[vector],
            n_results=5,
            include=["documents", "metadatas"]
        )

        api_data = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            api_data.append({
                "Formation": meta.get("Formation", doc),
                "Établissement": meta.get("Établissement", "Inconnu"),
                "Ville": meta.get("Ville", "Inconnue"),
                "Domaine": meta.get("Domaine", "Inconnu")
            })

        # 📚 Suggestions concrètes
        if api_data:
            api_data_summary = api_data[:3]
            formatted_infos = "\n".join(
                [f"- {formation['Formation']} à {formation['Établissement']} ({formation['Ville']})"
                for formation in api_data_summary if isinstance(formation, dict)]
            )
            context_elements.append(f"📚 Formations suggérées :\n{formatted_infos}")

    # 🔁 Reconstruit le contexte après ajout
    context = "\n".join(context_elements)

    # 🧠 Prompt intelligent
    prompt_template = f"""
Tu es un conseiller d'orientation scolaire bienveillant, précis, clair et proactif.

Contexte disponible :
{context}

Ta mission :
1. Si l'utilisateur semble perdu ou ne sait pas quoi faire, commence par lui poser les 3 questions suivantes :
   - Quel est ton âge ?
   - Quel est ton dernier diplôme obtenu ?
   - Où vis-tu actuellement (ville ou région) ?

2. Une fois ces infos connues, propose-lui 2 à 3 formations adaptées.

3. Ne répète JAMAIS une question déjà posée (analyse le contexte).

Utilisateur : {prompt}
Assistant :
""".strip()

    # ✂️ Découpe si trop long
    prompt_tokens = tokenizer(prompt_template).input_ids
    MAX_TOKENS = 450
    if len(prompt_tokens) > MAX_TOKENS:
        prompt_tokens = prompt_tokens[-MAX_TOKENS:]
        prompt_template = tokenizer.decode(prompt_tokens, skip_special_tokens=True)

    # 🧠 Appel du modèle
    response = model(prompt_template, max_new_tokens=300, temperature=0.7, repetition_penalty=1.15,
                    stop=["Utilisateur :", "Assistant :"])
    add_to_memory(prompt, response, embedding_model, collection)
    return response
