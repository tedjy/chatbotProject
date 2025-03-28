import requests
import time
import chromadb
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Initialisation
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
db_api = chromadb.PersistentClient(path="../chroma_api")
api_collection = db_api.get_or_create_collection("api_data")

api_url = "https://api.opendata.onisep.fr/downloads/5fa591127f501/5fa591127f501.json"

def log_erreur(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open("log_erreur.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
    print(message)

def fetch_json_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        if "application/json" not in response.headers.get("Content-Type", ""):
            log_erreur("❌ L'API ne retourne pas du JSON.")
            return []
        return response.json() if isinstance(response.json(), list) else []
    except Exception as e:
        log_erreur(f"❌ Erreur récupération JSON : {e}")
        return []

def scrap_etablissements_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        # Popup cookies
        try:
            deny_btn = driver.find_element(By.ID, "tarteaucitronAllDenied2")
            deny_btn.click()
            print("✅ Popup cookies fermée")
        except:
            pass

        current_url = driver.current_url
        print("🌐 URL chargée :", current_url)

        bouton_trouve = False
        for label in ["établissements", "Où se former", "Voir les lieux de formation"]:
            try:
                bouton = driver.find_element(By.PARTIAL_LINK_TEXT, label)
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, label)))
                driver.execute_script("arguments[0].scrollIntoView();", bouton)
                bouton.click()
                print(f"🖱️ Clic sur : {label}")
                bouton_trouve = True
                time.sleep(2)
                break
            except:
                continue

        if not bouton_trouve:
            log_erreur(f"⚠️ Aucun bouton cliquable trouvé sur : {url}")
            driver.quit()
            return []

        # Attente du tableau
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except TimeoutException:
            log_erreur(f"❌ Aucune table trouvée sur : {url}")
            driver.quit()
            return []

        etablissements = []
        page = 1

        while True:
            print(f"📄 Lecture page {page}...")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")
            if not table:
                log_erreur(f"❌ Aucune table visible sur : {url} (page {page})")
                break

            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    etab = cols[0].get_text(strip=True)
                    ville = cols[1].get_text(strip=True)
                    cp = cols[2].get_text(strip=True)
                    etablissements.append({
                        "etablissement": etab,
                        "ville": ville,
                        "code_postal": cp
                    })

            # Chercher bouton "page suivante"
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[aria-label="page suivante"]'))
                )

                # Vérifie si le lien pointe bien quelque part (pas juste "#" ou désactivé)
                if next_button.get_attribute("href") and "disabled" not in next_button.get_attribute("class"):
                    driver.execute_script("arguments[0].scrollIntoView();", next_button)
                    time.sleep(1)
                    next_button.click()
                    time.sleep(2)
                    page += 1
                else:
                    break
            except Exception:
                break  # Fin de la pagination

        driver.quit()
        print(f"✅ {len(etablissements)} établissements récupérés au total.")
        return etablissements

    except WebDriverException as e:
        log_erreur(f"❌ Erreur Selenium sur {url} : {e}")
        return []


def format_json_for_chroma_multiple(json_data, etablissements):
    documents = []
    code_scolarite = json_data.get("code_scolarite", "unknown")
    nom_formation = json_data.get("libelle_formation_principal", "Non renseigné")
    url_onisep = json_data.get("url_et_id_onisep", "")

    if not etablissements:
        documents.append({
            "doc_id": f"{code_scolarite}_noetab",
            "document": f"""
            Formation : {nom_formation}
            Type : {json_data.get("libelle_type_formation", "Non renseigné")} ({json_data.get("sigle_type_formation", "N/A")})
            Durée : {json_data.get("duree", "Non renseigné")}
            Niveau de sortie : {json_data.get("niveau_de_sortie_indicatif", "Non renseigné")}
            Certification : {json_data.get("libelle_niveau_de_certification", "Non renseigné")} (Niveau {json_data.get("niveau_de_certification", "N/A")})
            Établissement : Inconnu
            Ville : Inconnue
            Code postal : N/A
            Plus d'infos : {url_onisep}
            Domaine : {json_data.get("domainesous-domaine", "Non renseigné")}
            """.strip(),
            "metadata": {
                "code_scolarite": code_scolarite,
                "ville": "Inconnue",
                "etablissement": "Inconnu",
                "code_postal": "N/A"
            }
        })
    else:
        for etab in etablissements:
            doc_id = f"{code_scolarite}_{etab['code_postal']}_{etab['etablissement'].replace(' ', '_')}"
            documents.append({
                "doc_id": doc_id,
                "document": f"""
                Formation : {nom_formation}
                Type : {json_data.get("libelle_type_formation", "Non renseigné")} ({json_data.get("sigle_type_formation", "N/A")})
                Durée : {json_data.get("duree", "Non renseigné")}
                Niveau de sortie : {json_data.get("niveau_de_sortie_indicatif", "Non renseigné")}
                Certification : {json_data.get("libelle_niveau_de_certification", "Non renseigné")} (Niveau {json_data.get("niveau_de_certification", "N/A")})
                Établissement : {etab['etablissement']}
                Ville : {etab['ville']}
                Code postal : {etab['code_postal']}
                Plus d'infos : {url_onisep}
                Domaine : {json_data.get("domainesous-domaine", "Non renseigné")}
                """.strip(),
                "metadata": {
                    "code_scolarite": code_scolarite,
                    "ville": etab['ville'],
                    "etablissement": etab['etablissement'],
                    "code_postal": etab['code_postal']
                }
            })
    return documents

def store_api_data_in_chroma(json_data_list):
    if not json_data_list:
        print("⚠️ Aucune donnée API à stocker.")
        return

    ajoutées, doublons = 0, 0
    for json_data in json_data_list:
        url_onisep = json_data.get("url_et_id_onisep", "")
        etablissements = scrap_etablissements_selenium(url_onisep)
        docs = format_json_for_chroma_multiple(json_data, etablissements)

        for d in docs:
            try:
                vector = embedding_model.encode(d["document"]).tolist()
                api_collection.add(
                    documents=[d["document"]],
                    embeddings=[vector],
                    metadatas=[{**d["metadata"], "source": "API"}],
                    ids=[d["doc_id"]]
                )
                ajoutées += 1
            except Exception as e:
                log_erreur(f"⚠️ Doublon ou erreur sur {d['doc_id']} : {e}")
                doublons += 1
            time.sleep(0.2)

    print(f"✅ {ajoutées} documents ajoutés.")
    if doublons:
        print(f"⚠️ {doublons} doublons ignorés.")

if __name__ == "__main__":
    data = fetch_json_data(api_url)
    if data:
        store_api_data_in_chroma(data)
    else:
        log_erreur("❌ Impossible de récupérer les données ONISEP.")
