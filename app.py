import json
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Chargement des variables d'environnement locales si présentes
load_dotenv()

# ---------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Chatbot Sport Pro - RAG",
    page_icon="👟",
    layout="wide"
)

st.title("👟 Assistant Intelligent - Équipement Sportif & RAG")
st.write("Trouvez la paire parfaite grâce à notre conseiller IA connecté au catalogue en temps réel.")

# ---------------------------------------------------------
# 2. CHARGEMENT DU CATALOGUE
# ---------------------------------------------------------
@st.cache_data
def charger_catalogue():
    with open("Chaussures.json", "r", encoding="utf-8") as file:
        return json.load(file)

CATALOGUE = charger_catalogue()

# ---------------------------------------------------------
# 3. BARRE LATÉRALE (SIDEBAR) : RENDUE PRIORITAIRE
# ---------------------------------------------------------
st.sidebar.header("🎛️ Filtres & Options")

# Le filtre par budget intelligent (Slider)
prix_max = st.sidebar.slider(
    "💰 Budget maximum (€)", 
    min_value=50, 
    max_value=200, 
    value=160, 
    step=10
)

# Filtrer le catalogue en fonction du budget sélectionné
catalogue_filtre = [p for p in CATALOGUE if p["prix"] <= prix_max]

st.sidebar.markdown(f"**Produits disponibles :** {len(catalogue_filtre)} modèle(s)")

# Affichage des produits filtrés dans la sidebar avec leurs images
for produit in catalogue_filtre:
    with st.sidebar.expander(f"{produit['nom']} ({produit['prix']} €)"):
        if "image_url" in produit:
            st.image(produit["image_url"], use_container_width=True)
        st.write(f"**Activité :** {produit['activite']}")
        st.write(f"**Avantages :** {', '.join(produit['avantages'])}")

st.sidebar.markdown("---")

# Bouton de réinitialisation ("Clear Chat")
if st.sidebar.button("🗑️ Effacer la conversation", type="primary"):
    st.session_state.messages = []
    st.rerun()

# ---------------------------------------------------------
# 4. RÉCUPÉRATION DE LA CLÉ API (SÉCURISÉE)
# ---------------------------------------------------------
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    API_KEY = os.getenv("OPENAI_API_KEY")

# Si la clé est absente, on affiche un avertissement sans bloquer la sidebar
if not API_KEY or API_KEY == "TA_CLE_API_ICI":
    st.warning("⚠️ Clé API OpenAI introuvable. Configurez votre clé dans un fichier `.env` (`OPENAI_API_KEY=votre_cle`) pour activer les réponses de l'IA.")
    client = None
else:
    client = OpenAI(api_key=API_KEY)

# ---------------------------------------------------------
# 5. GESTION DE L'HISTORIQUE DE CONVERSATION (SESSION STATE)
# ---------------------------------------------------------
contexte_catalogue_filtre = json.dumps(catalogue_filtre, ensure_ascii=False, indent=2)

if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt = {
    "role": "system",
    "content": (
        "Tu es un conseiller commercial expert et chaleureux dans un magasin de sport. "
        f"Voici le catalogue filtré selon le budget de l'utilisateur ({prix_max} € max) :\n{contexte_catalogue_filtre}\n\n"
        "Ton rôle est d'aider l'utilisateur à choisir les chaussures adaptées à son besoin. "
        "Règles strictes :\n"
        "1. Ne recommande que des produits présents dans le catalogue filtré ci-dessus.\n"
        "2. Indique clairement le nom, le prix et les avantages des produits conseillés.\n"
        "3. Sois concis, poli et retiens le fil de la discussion."
    )
}

# Affichage de l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# 6. INTERACTIONS UTILISATEUR & APPEL LLM
# ---------------------------------------------------------
if user_input := st.chat_input("Ex: Je cherche des chaussures de randonnée étanches..."):
    
    if not client:
        st.error("Impossible de contacter l'IA : veuillez configurer votre clé API OpenAI.")
    else:
        # 1. Enregistrement et affichage du message utilisateur
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Construction de la liste des messages pour l'API
        messages_pour_ia = [system_prompt] + st.session_state.messages

        # 3. Génération de la réponse
        with st.chat_message("assistant"):
            with st.spinner("Le conseiller analyse le catalogue..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages_pour_ia,
                        temperature=0.3
                    )
                    reponse_ia = response.choices[0].message.content
                    st.markdown(reponse_ia)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
                    
                except Exception as e:
                    st.error(f"Une erreur est survenue : {e}")