import asyncio
import sys
import streamlit as st
# from onisepData import JSONtoChroma
from components.loadModel import load_model
from components.initialize import initialize
from components.interface import interface


api_url =  "https://api.opendata.onisep.fr/downloads/5fa591127f501/5fa591127f501.json"
    
# Correction pour éviter RuntimeError sur Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

st.write("💾 Utilisation de la mémoire RAG")

# Chargement du model 
model, tokenizer = load_model()
# Initialisation
embedding_model, collection, api_collection = initialize()


# interface streamlit
interface(model, tokenizer, embedding_model, collection, api_collection)




# fetch l'api de l'onisep
# JSONtoChroma.fetch_json_data()


