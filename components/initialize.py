from sentence_transformers import SentenceTransformer
import chromadb
#  Initialiser la base mémoire
def initialize():
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    db_conversations = chromadb.PersistentClient(path="./chroma_conversations")
    db_api = chromadb.PersistentClient(path="./chroma_api")
    # collection pour les conversation
    collection = db_conversations.get_or_create_collection("chat_memory")
    # collection pour les données de l'api
    api_collection = db_api.get_or_create_collection("api_data")

    # 🔹 On retourne tout ce dont on a besoin
    return embedding_model, collection, api_collection
