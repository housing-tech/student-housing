import streamlit as st
from housing.universities import get_all_universities
from housing.matching import get_matches
from housing.listings import add_listing

import qrcode
from io import BytesIO

# ✅ Public URL (Streamlit Cloud)
PUBLIC_URL = "https://student-housing-nvaq8qkrfhc4trzuvkgmnc.streamlit.app"

st.set_page_config(page_title="Student Housing", layout="centered")
st.title("🏠 Student Housing")

# ✅ Streamlit query param okuma (sürüm farklarını tolere eder)
try:
    mode_param = st.query_params.get("mode")
except Exception:
    mode_param = st.experimental_get_query_params().get("mode")

if isinstance(mode_param, list):
    mode_param = mode_param[0] if mode_param else None

default_index = 1 if mode_param == "owner" else 0

mode = st.sidebar.radio(
    "Mode",
    ["Étudiant", "Propriétaire (QR)"],
    index=default_index
)

# ✅ QR kod: artık herkesin açabileceği PUBLIC URL
st.sidebar.markdown("### 📱 QR Code (Propriétaire)")
owner_url = f"{PUBLIC_URL}/?mode=owner"

qr = qrcode.make(owner_url)
buf = BytesIO()
qr.save(buf, format="PNG")
buf.seek(0)  # ✅ iyi pratik
st.sidebar.image(buf, caption="Scanner pour publier un logement")
st.sidebar.caption(owner_url)


def build_uni_select(unis, label_title: str):
    """Dropdown’da kullanıcıya güzel label gösterip, id döndürür."""
    label_to_id = {}
    for u in unis:
        arr = u.get("arrondissement")
        if arr:
            label = f"{u['nom']} ({arr})"
        else:
            label = u["nom"]
        label_to_id[label] = u["id"]

    selected_label = st.selectbox(label_title, list(label_to_id.keys()))
    return label_to_id[selected_label]


# -------- OWNER (QR) MODE --------
if mode == "Propriétaire (QR)":
    st.header("🏷️ Ajouter un logement")
    st.caption("Publiez un logement pour les étudiants")

    unis = get_all_universities()
    universite = build_uni_select(unis, "Université ciblée")

    st.divider()

    nom = st.text_input("Nom du logement *")

    distance_km = st.slider(
        "Distance de l'université (km)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.1
    )

    col1, col2 = st.columns(2)
    with col1:
        loyer_min = st.number_input("Loyer minimum (€)", min_value=0, max_value=2000, value=400, step=50)
    with col2:
        loyer_max = st.number_input("Loyer maximum (€)", min_value=0, max_value=2000, value=800, step=50)

    if loyer_max < loyer_min:
        st.warning("⚠️ Le loyer maximum doit être supérieur ou égal au loyer minimum.")

    type_logement = st.selectbox(
        "Type de logement",
        ["Studio", "Appartement 1 chambre", "Colocation (2+ personnes)"]
    )

    meubles = st.checkbox("Meublé")
    charges_incluses = st.checkbox("Charges incluses")

    st.divider()

    st.subheader("👤 Propriétaire & contact")
    proprietaire = st.text_input("Nom du propriétaire *")
    contact_tel = st.text_input("Téléphone")
    contact_email = st.text_input("Email")
    contact_pref = st.selectbox("Contact préféré", ["Téléphone", "Email", "WhatsApp"])
    whatsapp = st.text_input("WhatsApp (optionnel)")

    st.divider()

    st.subheader("📝 Détails")
    adresse_quartier = st.text_input("Adresse / Quartier (optionnel)")
    disponible = st.date_input("Disponible à partir du")
    description = st.text_area(
        "Description (optionnel)",
        placeholder="Ex: proche métro, calme, internet inclus, etc."
    )
    regles = st.multiselect(
        "Règles (optionnel)",
        ["Non-fumeur", "Animaux acceptés", "Étudiants uniquement", "Garantie demandée"]
    )

    if st.button("📤 Publier le logement"):
        if not nom.strip() or not proprietaire.strip():
            st.error("❌ Champs obligatoires: Nom du logement et Nom du propriétaire.")
        elif loyer_max < loyer_min:
            st.error("❌ Le loyer maximum doit être ≥ au loyer minimum.")
        else:
            created = add_listing({
                "universite": universite,
                "nom": nom.strip(),
                "distance_km": float(distance_km),

                "loyer_min": int(loyer_min),
                "loyer_max": int(loyer_max),
                "type": type_logement,
                "meubles": bool(meubles),
                "charges_incluses": bool(charges_incluses),

                "proprietaire": proprietaire.strip(),
                "telephone": contact_tel.strip(),
                "email": contact_email.strip(),
                "contact_pref": contact_pref,
                "whatsapp": whatsapp.strip(),

                "quartier": adresse_quartier.strip(),
                "disponible": str(disponible),
                "description": description.strip(),
                "regles": regles,
            })

            st.success(f"✅ Logement ajouté ! (id = {created['id']})")
            st.info("Passe en mode Étudiant pour voir l’annonce apparaître.")

    st.stop()


# -------- ÉTUDIANT MODE --------
unis = get_all_universities()
uni_id = build_uni_select(unis, "Choisis ton université")

max_km = st.slider("Distance max (km)", 0.0, 10.0, 3.0, 0.5)

colA, colB = st.columns(2)
with colA:
    budget_min = st.number_input("Budget min (€)", 0, 2000, 0, 50)
with colB:
    budget_max = st.number_input("Budget max (€)", 0, 2000, 1200, 50)

if budget_max < budget_min:
    st.warning("⚠️ Le budget max doit être ≥ au budget min.")

types_filter = st.multiselect(
    "Type souhaité",
    ["Studio", "Appartement 1 chambre", "Colocation (2+ personnes)"],
    default=[]
)

matches = get_matches(uni_id, max_km=max_km)


def listing_budget_ok(l):
    if budget_max < budget_min:
        return False

    # Eski datayla uyum
    if "loyer" in l:
        val = int(l["loyer"])
        return budget_min <= val <= budget_max

    # Yeni datayla uyum
    lo_min = int(l.get("loyer_min", 0))
    lo_max = int(l.get("loyer_max", lo_min))
    return not (lo_max < budget_min or lo_min > budget_max)


def listing_type_ok(l):
    if not types_filter:
        return True
    return l.get("type") in types_filter or l.get("type_logement") in types_filter


filtered = [l for l in matches if listing_budget_ok(l) and listing_type_ok(l)]

st.subheader("Résultats")
if not filtered:
    st.info("Aucun logement trouvé.")
else:
    for l in filtered:
        with st.container(border=True):
            st.write(f"**{l.get('nom', '')}**")
            st.write(f"📍 {l.get('distance_km', '?')} km")

            if "loyer" in l:
                st.write(f"💶 {l['loyer']} €")
            else:
                st.write(f"💶 {l.get('loyer_min', '?')}–{l.get('loyer_max', '?')} €")

            st.write(f"🛏️ {l.get('type', '')}")

            if l.get("meubles"):
                st.write("🪑 Meublé")
            if l.get("charges_incluses"):
                st.write("⚡ Charges incluses")
            if l.get("quartier"):
                st.write(f"📌 {l['quartier']}")
            if l.get("disponible"):
                st.write(f"📅 Disponible: {l['disponible']}")

            contact_lines = []
            if l.get("proprietaire"):
                contact_lines.append(f"👤 {l['proprietaire']}")
            if l.get("telephone"):
                contact_lines.append(f"📞 {l['telephone']}")
            if l.get("email"):
                contact_lines.append(f"✉️ {l['email']}")
            if l.get("whatsapp"):
                contact_lines.append(f"💬 WhatsApp: {l['whatsapp']}")
            if l.get("contact"):
                contact_lines.append(f"📞 {l['contact']}")

            if contact_lines:
                st.write("\n\n".join(contact_lines))
