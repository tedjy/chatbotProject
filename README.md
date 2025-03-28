---
title: IAvenirChatbot
emoji: 👁
colorFrom: blue
colorTo: red
sdk: streamlit
sdk_version: 1.42.2
app_file: app.py
pinned: false
---
# 🤖 IAvenir Chatbot – Assistant d'orientation scolaire intelligent (Local)

Bienvenue dans **IAvenir**, un chatbot intelligent conçu pour aider les lycéens et étudiants à s’orienter grâce à :

✅ Un modèle local (Mistral 7B GGUF)  
✅ Une mémoire vectorielle (ChromaDB)  
✅ Des suggestions de formations et métiers  
✅ Un quiz d’orientation intégré 🎓

---

## 🚀 Installation en local

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-utilisateur/IAvenirChatbot.git
cd IAvenirChatbot
```
### 2. Activer l’environnement virtuel
Sous Windows :
```bash
.venv\Scripts\activate
```
Sous macOS / Linux :
```bash
source .venv/bin/activate
```
### 3. Vérifier que le modèle Mistral est bien téléchargé
Le fichier suivant doit être présent dans le dossier models/ :
```bash
models/mistral-7b-instruct-v0.1.Q8_0.gguf
```
 Si ce n’est pas encore fait, télécharge-le depuis :

Hugging Face – TheBloke/Mistral-7B-Instruct-v0.1-GGUF

### 4. Lancer l'application avec Streamlit
Dans le terminal, exécute :

```bash
streamlit run index.py
```
