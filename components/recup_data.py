from components.initialize import initialize
import json
from rapidfuzz import process
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

    return formatted_memory  # Liste de str  # ✅ Liste de chaînes prêtes à afficher
    # if results["documents"] and len(results["documents"][0]) > 0:
    #     return results["documents"][0][0]  # Retourne le souvenir trouvé
    # else:
    #     print(" Aucun souvenir trouvé.")
    #     return None

def retrieve_api_data(user_input, embedding_model, api_collection):
    """Recherche dans la mémoire des formations API en s'assurant de la pertinence"""
    vector = embedding_model.encode(user_input).tolist()
    results = api_collection.query(query_embeddings=[vector], n_results=3, include=["documents", "metadatas"], where={"source": "API"})
    
    api_results = []
    if results["documents"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            api_results.append({
                "Formation": meta.get("Formation", doc),
                "Établissement": meta.get("Établissement", "Inconnu"),
                "Ville": meta.get("Ville", "Inconnue"), 
                "Domaine": meta.get("Domaine", "Inconnue")
 # lien vers la fiche ONISEP
            })

    return api_results  # Maintenant une liste de dictionnaires
    
def trouver_diplome(user_input, reference_diplomes):
    input_clean = user_input.lower()
    result = process.extractOne(input_clean, reference_diplomes.keys())
    
    if result is not None:
        match, score, _ = result
        if score > 80:
            return match, reference_diplomes[match]
    
    return None, None