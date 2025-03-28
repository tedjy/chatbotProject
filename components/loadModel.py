import streamlit as st
from ctransformers import AutoModelForCausalLM
from transformers import AutoTokenizer
#  Charger le modèle GGUF
MODEL_PATH = "models/mistral-7b-instruct-v0.1.Q8_0.gguf"
HF_TOKENIZER_NAME = "mistralai/Mistral-7B-v0.1"
@st.cache_resource
def load_model():
    """Charger Mistral-7B GGUF pour CPU"""
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="mistral",
        gpu_layers=0
    )
    tokenizer = AutoTokenizer.from_pretrained(HF_TOKENIZER_NAME)
    return model, tokenizer
try:
    model = load_model()
    st.success(f" Modèle chargé avec succès !")
except Exception as e:
    st.error(f" Erreur lors du chargement du modèle : {e}")