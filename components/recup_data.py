from components.initialize import initialize
import json
from rapidfuzz import process, fuzz
# Initialisation
embedding_model, collection, api_collection = initialize()

def retrieve_memory(user_input, embedding_model, collection, max_memories=3):
    """Récupère les dernières conversations enregistrées (par date)"""
    all_data = collection.get(include=["documents", "metadatas"])
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]

    # Trie tous les souvenirs par timestamp (du plus ancien au plus récent)
    sorted_docs = sorted(
        zip(documents, metadatas),
        key=lambda x: x[1].get("timestamp", "1970-01-01T00:00:00")
    )

    # Garde les N derniers (par défaut 3)
    selected_docs = sorted_docs[-max_memories:]

    formatted_memory = []
    for doc, meta in selected_docs:
        try:
            doc_str = doc[0] if isinstance(doc, tuple) else doc
            messages = json.loads(doc_str)
            lines = [f"{m['role'].capitalize()} : {m['content']}" for m in messages]
            formatted_memory.append("\n".join(lines))
        except Exception as e:
            print("❌ Erreur de parsing mémoire :", e)
            formatted_memory.append(str(doc))

    return formatted_memory  # Liste de str  # 

def retrieve_api_data(user_input, embedding_model, api_collection): 
    """Recherche dans la mémoire des formations API avec extraction correcte des métadonnées"""
    vector = embedding_model.encode(user_input).tolist()
    results = api_collection.query(query_embeddings=[vector], n_results=10, include=["documents", "metadatas"], where={"source": "API"})
    
    api_results = []

    if results["documents"]:
        for doc in results["documents"][0]:
            lignes = doc.split("\n")
            item = {}
            for ligne in lignes:
                if ":" in ligne:
                    cle, val = ligne.split(":", 1)
                    item[cle.strip()] = val.strip()
            api_results.append({
                "Formation": item.get("Formation", "Inconnu"),
                "Établissement": item.get("Établissement", "Inconnu"),
                "Ville": item.get("Ville", "Inconnue"),
                "Code postal": item.get("Code postal", ""),
                "Domaine": item.get("Domaine", "Inconnu"),
                "Niveau de sortie": item.get("Niveau de sortie", "Inconnu"),
                "Durée": item.get("Durée", ""),
                "Plus d'infos": item.get("Plus d'infos", "")
            })
    
    return api_results
    
def trouver_diplome(prompt, diplomes_reference):
    """
    Essaie de détecter un diplôme mentionné dans le prompt de l'utilisateur,
    en comparant avec les noms de formations de l'API (diplomes_reference).
    """
    prompt_clean = prompt.lower()

    if not diplomes_reference:
        return None, None

    # On cherche la formation la plus proche du prompt (fuzzy matching)
    meilleur_match = process.extractOne(
        prompt_clean,
        diplomes_reference.keys(),
        scorer=fuzz.token_sort_ratio  # ✅ et pas process.fuzz
    )

    if meilleur_match and meilleur_match[1] > 75:  # seuil de confiance
        nom_formation = meilleur_match[0]
        infos = diplomes_reference[nom_formation]
        return nom_formation, infos

    return None, None