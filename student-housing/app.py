import streamlit as st
from housing.universities import get_all_universities
from housing.matching import get_matches
from housing.listings import add_listing

import qrcode
from io import BytesIO

# ✅ Burayı kendi Mac IP'n ile değiştir (Terminalde "Network URL" yazan)
SERVER_IP = "10.182.186.198"
PORT = 8501

st.set_page_config(page_title="Student Housing", layout="centered")
st.title("🏠 Student Housing")

# ✅ Streamlit query param okuma (sürüm farklarını tolere eder)
try:
    mode_param = st.query_params.get("mode")
except Exception:
    mode_param = st.experimental_get_query_params().get("mode")

# mode_param bazen list gelebiliyor
if isinstance(mode_param, list):
    mode_param = mode_param[0]

default_index = 1 if mode_param == "owner" else 0

mode = st.sidebar.radio(
    "Mode",
    ["Étudiant", "Propriétaire (QR)"],
    index=default_index
)

# ✅ QR kod: Telefonda çalışması için localhost değil IP olmalı
st.sidebar.markdown("### 📱 QR Code (Propriétaire)")
owner_url = f"http://{SERVER_IP}:{PORT}/?mode=owner"

qr = qrcode.make(owner_url)
buf = BytesIO()
qr.save(buf, format="PNG")
st.sidebar.image(buf.getvalue(), caption="Scanner pour publier un logement")
st.sidebar.caption(owner_url)

# -------- OWNER (QR) MODE --------
if mode == "Propriétaire (QR)":
    st.header("🏷️ Ajouter un logement")
    st.caption("Accès via QR code (simulation)")

    unis = get_all_universities()
    uni_ids = [u["id"] for u in unis]
    universite = st.selectbox("Université ciblée", uni_ids)

    nom = st.text_input("Nom du logement")
    distance_km = st.number_input("Distance (km)", 0.0, 50.0, 1.0, 0.1)
    loyer = st.number_input("Loyer (€)", 0, 5000, 600, 10)
    typ = st.selectbox("Type", ["Studio", "Partagé"])
    contact = st.text_input("Contact")

    if st.button("Publier"):
        if nom.strip() and contact.strip():
            created = add_listing({
                "universite": universite,
                "nom": nom.strip(),
                "distance_km": float(distance_km),
                "loyer": int(loyer),
                "type": typ,
                "contact": contact.strip()
            })
            st.success(f"✅ Logement ajouté ! (id = {created['id']})")
            st.info("Passe en mode Étudiant pour voir l’annonce apparaître.")
        else:
            st.error("Nom et contact obligatoires.")

    st.stop()

# -------- ÉTUDIANT MODE --------
unis = get_all_universities()
labels = [f"{u['id']} - {u['nom']}" for u in unis]
selected = st.selectbox("Choisis ton université", labels)

max_km = st.slider("Distance max (km)", 1.0, 10.0, 3.0, 0.5)
uni_id = selected.split(" - ")[0]

matches = get_matches(uni_id, max_km=max_km)

st.subheader("Résultats")
if not matches:
    st.info("Aucun logement trouvé.")
else:
    for l in matches:
        with st.container(border=True):
            st.write(f"**{l['nom']}**")
            st.write(f"📍 {l['distance_km']} km | 💶 {l['loyer']} €")
            st.write(f"🛏️ {l['type']}")
            st.write(f"📞 {l['contact']}")
            Move app.py to root
