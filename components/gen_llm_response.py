from components.initialize import initialize
from components.recup_data import retrieve_api_data, retrieve_memory, trouver_diplome
from components.addToMemory import add_to_memory
# import streamlit as st
# from components.addToMemory import extraire_reponse_propre
import re
# import unicodedata
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialisation des modèles et des bases vectorielles (mémoires + données ONISEP)
embedding_model, collection, api_collection = initialize()

def generate_llm_response(prompt, model_fn, embedding_model, collection, api_collection):

    def nettoyer_texte(txt):
        txt = re.sub(r'\s+-\s+', '\n- ', txt)
        txt = re.sub(r'\s{2,}', ' ', txt)
        txt = re.sub(r'\n{3,}', '\n\n', txt)
        txt = re.sub(r'(?<=[.,])(?=[^\s])', ' ', txt)
        txt = re.sub(r'\s+([.,])', r'\1', txt)
        return txt.strip()

    def extraire_niveau(s):
        if not s: return None
        match = re.search(r"bac\s*\+ *\d", s.lower())
        if match:
            return match.group().replace(" ", "")
        elif "cap" in s.lower():
            return "CAP"
        elif "bac pro" in s.lower():
            return "bac"
        return None

    def niveau_est_superieur(niveau_actuel, niveau_cible):
        niveaux_ordres = ["CAP", "bac", "bac+2", "bac+3", "bac+5", "bac+8"]
        na = extraire_niveau(niveau_actuel)
        nc = extraire_niveau(niveau_cible)
        try:
            return niveaux_ordres.index(nc) > niveaux_ordres.index(na)
        except:
            return False

    def trouver_diplome_approx(user_text, diplomes_ref, embedding_model):
        keys = list(diplomes_ref.keys())
        if not keys:
            return False, None
        user_emb = embedding_model.encode(user_text.lower()).reshape(1, -1)
        diplome_embs = embedding_model.encode(keys)
        sims = cosine_similarity(user_emb, diplome_embs)[0]
        best_idx = int(np.argmax(sims))
        if sims[best_idx] > 0.55:
            best_key = keys[best_idx]
            return True, diplomes_ref[best_key]
        return False, None

    prompt = re.sub(r"(parle[- ]?moi.*fran[cç]ais|speak french)", "", prompt, flags=re.IGNORECASE).strip()

    memory = retrieve_memory(prompt, embedding_model, collection)
    api_data = retrieve_api_data(prompt, embedding_model, api_collection)

    etablissements_par_formation = {}
    diplomes_reference = {}
    domaines_detectes = set()
    context_elements = []

    for item in api_data:
        ville = item.get("Ville", "Inconnue").lower()
        etablissement = item.get("Établissement", "Établissement inconnu")
        lien = item.get("Plus d'infos", "")
        domaine = item.get("Domaine", "").lower()
        formation = item.get("Formation", "").lower()

        if formation not in etablissements_par_formation:
            etablissements_par_formation[formation] = []
        etablissements_par_formation[formation].append(item)

        if any(x in formation for x in ["bts", "bac pro", "cap", "licence", "master"]):
            diplomes_reference[formation] = {
                "niveau": item.get("Niveau de sortie", "inconnu"),
                "domaine": domaine
            }

        if domaine:
            domaines_detectes.add(domaine)

    infos = {
        "age": any(x in prompt.lower() for x in ["ans", "âge", "j'ai 2", "j'ai 1", "j'ai 3"]),
        "diplome": any(x in prompt.lower() for x in ["bts", "bac", "cap", "licence", "master"]),
        "ville": any(x in prompt.lower() for x in ["paris", "lille", "lyon", "ville", "marseille", "roubaix"])
    }

    villes_connues = set(f.get("Ville", "").lower() for f in api_data if f.get("Ville"))
    texte_utilisateur = prompt.lower()
    ville_utilisateur = next((ville for ville in villes_connues if ville in texte_utilisateur), None)

    match_diplome, infos_diplome = trouver_diplome_approx(prompt, diplomes_reference, embedding_model)

    domaine_utilisateur = ""
    for d in domaines_detectes:
        if d in texte_utilisateur:
            domaine_utilisateur = d
            break
    if not domaine_utilisateur and infos_diplome:
        domaine_utilisateur = infos_diplome["domaine"].split("/")[0].lower()

    niveau_utilisateur = infos_diplome["niveau"] if infos_diplome else "bac"

    formations_filtrees = []
    if infos["age"] and infos["diplome"] and infos["ville"] and (match_diplome or domaine_utilisateur):
        formations_filtrees = [
            f for f in api_data
            if domaine_utilisateur in f.get("Domaine", "").lower()
            and niveau_est_superieur(niveau_utilisateur, f.get("Niveau de sortie", ""))
            and (not ville_utilisateur or ville_utilisateur in f.get("Ville", "").lower())
        ]
        if not formations_filtrees:
            formations_filtrees = [
                f for f in api_data
                if niveau_est_superieur(niveau_utilisateur, f.get("Niveau de sortie", ""))
                and (not ville_utilisateur or ville_utilisateur in f.get("Ville", "").lower())
            ]

        if formations_filtrees:
            formatted_infos = "\n\n".join([
                f"📚 **{f.get('Formation', 'Formation inconnue')}**\n"
                f"🏫 Établissement : *{f.get('Établissement', 'Établissement inconnu')}*\n"
                f"📍 Ville : {f.get('Ville', 'Ville inconnue')} ({f.get('Code postal', '')})\n"
                f"🎓 Niveau : {f.get('Niveau de sortie', 'Non précisé')}\n"
                f"⏳ Durée : {f.get('Durée', 'Inconnue')}\n"
                f"🔗 [Plus d'infos]({(f.get('Plus d\'infos') or '').strip()})"
                for f in formations_filtrees[:6]
            ])
            context_elements.append(f"📚 Formations adaptées à ton diplôme :\n{formatted_infos}")

            formations_unique = list({f.get("Formation", "").lower() for f in formations_filtrees})
            for formation in formations_unique:
                etabs = etablissements_par_formation.get(formation, [])
                if etabs:
                    etabs_list = "\n".join([
                        f"🏫 {e.get('Établissement')} ({e.get('Ville')})"
                        for e in etabs if not ville_utilisateur or ville_utilisateur in e.get("Ville", "").lower()
                    ][:5])
                    context_elements.append(f"🏫 Établissements pour la formation **{formation}** :\n{etabs_list}")
    else:
        context_elements.append("❗Aucune formation spécifique trouvée à partir des informations données. N'hésite pas à préciser ton domaine ou ton diplôme.")

    questions = []
    if not infos["age"]: questions.append("- Quel est ton âge ?")
    if not infos["diplome"]: questions.append("- Quel est ton dernier diplôme obtenu ?")
    if not infos["ville"]: questions.append("- Dans quelle ville vis-tu ?")
    if questions:
        context_elements.insert(0, "📝 Pour mieux t'aider, j'ai besoin de connaître :\n" + "\n".join(questions))

    if memory and isinstance(memory[-1], str):
        dernier_msg = memory[-1].strip()
        if len(dernier_msg) < 800:
            context_elements.append("🧠 Historique :\n" + dernier_msg)

    context = "\n\n".join(context_elements)

    prompt_template = f"""### Instruction:
Tu es un assistant d’orientation scolaire bienveillant. Tu t'exprimes TOUJOURS en français, même si l’utilisateur mentionne une autre langue ou demande un changement.
Tu n’as pas le droit d’inventer de formations, d’établissements ou de liens.
Tu dois utiliser UNIQUEMENT les données présentes dans le contexte ci-dessous.
Si des formations ou établissements sont listés, affiche-les clairement, sans répétition.
Présente chaque formation en respectant exactement le format Markdown fourni.
Si rien n’est disponible, propose à l’utilisateur de reformuler sa demande ou de préciser son domaine ou diplôme.

### Contexte :
{context}

### Question :
{prompt}

### Réponse :
"""

    response_brute = model_fn(prompt_template)
    response_brute = nettoyer_texte(response_brute)

    if not response_brute or response_brute.strip() == "":
        return "❌ Réponse vide."
    if response_brute.startswith("❌") or "Erreur" in response_brute:
        return response_brute

    add_to_memory(prompt, response_brute, embedding_model, collection)
    return response_brute
