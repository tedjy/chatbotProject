# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from bs4 import BeautifulSoup
# import time
# import json

# def scraper_etablissements_roubaix(url, ville_cible="roubaix"):
#     # Options pour navigateur sans interface graphique
#     options = Options()
#     options.headless = True
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     # Lance Chrome via Selenium
#     driver = webdriver.Chrome(options=options)
#     driver.get(url)

#     time.sleep(4)  # attend le chargement JS

#     # Récupère le HTML final
#     soup = BeautifulSoup(driver.page_source, "html.parser")
#     driver.quit()

#     # Extraction du tableau
#     table = soup.find("table")
#     if not table:
#         print("❌ Aucun tableau trouvé.")
#         return []

#     rows = table.find_all("tr")[1:]  # skip header
#     etablissements = []

#     for row in rows:
#         cols = row.find_all("td")
#         if len(cols) >= 3:
#             etablissement = cols[0].get_text(strip=True)
#             ville = cols[1].get_text(strip=True).lower()
#             code_postal = cols[2].get_text(strip=True)

#             if ville_cible.lower() in ville:
#                 etablissements.append({
#                     "etablissement": etablissement,
#                     "ville": ville,
#                     "code_postal": code_postal
#                 })

#     return etablissements

# # URL de la page ONISEP contenant la liste (exemple à remplacer par ton lien)
# url_onisep = "https://www.onisep.fr/recherche/formations?item=FOR.1234"  # <-- à adapter

# # Scrape Roubaix uniquement
# resultats = scraper_etablissements_roubaix(url_onisep, ville_cible="roubaix")

# # Enregistrement dans un fichier JSON
# with open("etablissements_roubaix.json", "w", encoding="utf-8") as f:
#     json.dump(resultats, f, ensure_ascii=False, indent=2)

# print(f"✅ {len(resultats)} établissements trouvés à Roubaix.")

# def enrichir_formation(formation):
#     lieu, etab = get_lieu_etablissement_from_url(formation["url"])
#     if not lieu or not etab:
#         return None  # skip les erreurs

#     texte_enrichi = (
#         f"Formation : {formation['intitule']}\n"
#         f"Type : {formation['type']}\n"
#         f"Durée : {formation['duree']}\n"
#         f"Niveau de sortie : {formation['niveau_sortie']}\n"
#         f"Certification : {formation['certification']}\n"
#         f"Domaine : {formation['domaine']}\n"
#         f"Établissement : {etab}\n"
#         f"Lieu : {lieu}\n"
#         f"Plus d'infos : {formation['url']}"
#     )
#     return texte_enrichi, etab, lieu


# def injecter_formations_enrichies(formations, embedding_model, api_collection):
#     for i, f in enumerate(formations):
#         texte, etab, lieu = enrichir_formation(f)
#         if texte:
#             vector = embedding_model.encode(texte).tolist()
#             api_collection.add(
#                 documents=[texte],
#                 embeddings=[vector],
#                 metadatas=[{
#                     "intitule": f["intitule"],
#                     "etablissement": etab,
#                     "ville": lieu,
#                     "slug": f["slug"]
#                 }],
#                 ids=[f"formation_{i}"]
#             )
#             print(f"✅ Formation injectée : {f['intitule']} à {lieu}")
# # 

