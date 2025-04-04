import json
from components.initialize import initialize
import datetime 
import uuid 
import re
# Initialisation
embedding_model, collection, api_collection = initialize()

def extraire_reponse_propre(output):
    """Nettoie et isole le texte de l’assistant depuis la sortie brute de llama.cpp"""
    if not output:
        return None
    if any(c in output for c in ["�", "領", "Ã"]):
        print("⚠️ Réponse corrompue détectée :", output)
        return None
    # 🔍 Recherche des balises les plus fréquentes
    patterns = [
        r"Machine :(.+)", 
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.DOTALL)
        if match:
            return match.group(1).strip()

    # On coupe dès qu'on voit que le modèle repart sur User :
    if "User :" in output:
        output = output.split("User :")[0]

    if "Machine :" in output:
        return output.split("Machine :")[-1].strip()
    
    output = output.split("User :")[0]  # stop avant que l’utilisateur parle de nouveau
    # Fallback nettoyage
    lines = output.strip().splitlines()
    cleaned = "\n".join([
        line for line in lines
        if not line.startswith("main:") and not line.startswith("<s>") and "-n" not in line
        and not line.startswith("# User") and not line.startswith("llama_")
    ])
    return cleaned.strip() if cleaned else None

# def add_to_memory(user_input, response, embedding_model, collection, role="Machine", source="conversation"):
#     # Nettoyage de la réponse
#     cleaned_response = extraire_reponse_propre(response)

#     if not cleaned_response or cleaned_response.startswith("❌") or cleaned_response.startswith("⏱️"):
#         print("🚫 Réponse ignorée (erreur ou vide)")
#         return

#     message_pair = [
#         {"role": "user", "content": user_input},
#         {"role": role, "content": cleaned_response}
#     ]

#     document_json = json.dumps(message_pair, ensure_ascii=False)
#     vector = embedding_model.encode(document_json).tolist()
#     memory_id = str(uuid.uuid4())
#     timestamp = datetime.datetime.now().isoformat()

#     print(f"📝 Ajout en mémoire : {document_json}")

#     collection.add(
#         documents=[document_json],
#         embeddings=[vector],
#         metadatas=[{
#             "source": source,
#             "timestamp": timestamp
#         }],
#         ids=[memory_id]
#     )

#     print(f"📌 Nombre total de conversations enregistrées : {len(collection.get()['ids'])}")

def add_to_memory(user_input, response, embedding_model, collection, role="assistant", source="conversation"):
    message_pair = [
        {"role": "user", "content": user_input},
        {"role": role, "content": response}
    ]
    document_json = json.dumps(message_pair, ensure_ascii=False)
    vector = embedding_model.encode(document_json).tolist()
    memory_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    print(f"📝 Ajout en mémoire : {document_json}")

    collection.add(
        documents=[document_json],
        embeddings=[vector],
        metadatas=[{
            "source": source,
            "timestamp": timestamp
        }],
        ids=[memory_id]
    )

    nb_conversations = len(collection.get()['ids']) if collection.get() and 'ids' in collection.get() else 0
    print(f"📌 Nombre total de conversations enregistrées : {nb_conversations}")

    
# with open("./jsonData/conversations_entrainement.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# for bloc in data:
#     conv = bloc.get("conversations", [])
#     for i in range(len(conv) - 1):
#         user_msg = conv[i]
#         assistant_msg = conv[i + 1]

#         if user_msg["role"] == "user" and assistant_msg["role"] == "assistant":
#             add_to_memory(user_msg["content"], assistant_msg["content"], embedding_model, collection, source="training")
