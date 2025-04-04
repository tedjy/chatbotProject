import streamlit as st
from llama_cpp import Llama
import os

# from ctransformers import AutoModelForCausalLM
# from transformers import AutoTokenizer
#  Charger le modèle GGUF

MODEL_PATH = "./models/mistral-7b-instruct-v0.1.Q8_0.gguf"
# HF_TOKENIZER_NAME = "mistralai/Mistral-7B-v0.1"
@st.cache_resource
def load_llama_model():
    return Llama(
        model_path=MODEL_PATH,
        n_ctx=32768,
        n_threads=os.cpu_count(),  # adapte selon ta machine
        verbose=False
    )

@st.cache_resource
def generate_with_llama(prompt: str) -> str:
    """Appelle llama_cpp avec découpage propre de la réponse après 'Machine :'."""
    llama = load_llama_model()

    nb_tokens_prompt = len(prompt.split())
    n_predict = max(300, min(1500, nb_tokens_prompt * 5))

    try:
        response = llama(
        prompt,
        max_tokens=n_predict,  # limite stricte
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        stop=["User :", "###"]
    )

        raw_output = response["choices"][0]["text"].strip()

        # ✅ Découpage intelligent
        if "Machine :" in raw_output:
            answer = raw_output.split("Machine :")[-1].strip()
        else:
            answer = raw_output.strip()

        if not answer:
            return "❌ Réponse vide."

        return answer

    except Exception as e:
        return f"❌ Erreur avec llama_cpp : {e}"
    