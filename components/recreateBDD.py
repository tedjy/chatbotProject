import os 
import shutil

def recreate():
    # ✅ Supprimer la base ChromaDB actuelle (qui mélange tout)
    # if os.path.exists("./chroma_conversations"):
    #     shutil.rmtree("./chroma_conversations")
    #     print("🗑️ Base de données ChromaDB supprimée !")
    
    if os.path.exists("../chroma_api"):
        shutil.rmtree("../chroma_api")
        print("🗑️ Base de données ChromaDB supprimée !")


recreate()

