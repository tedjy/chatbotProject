import json
from components.initialize import initialize
import datetime 
import uuid 
# Initialisation
embedding_model, collection, api_collection = initialize()

with open("./jsonData/conversations.json", "r", encoding="utf-8") as f:
    data = json.load(f)

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

    print(f"📌 Nombre total de conversations enregistrées : {len(collection.get()['ids'])}")

