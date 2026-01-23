import streamlit as st
from housing.universities import get_all_universities
from housing.matching import get_matches
from housing.listings import add_listing

import qrcode
from io import BytesIO
import pandas as pd
import requests

# ✅ Public URL (Streamlit Cloud)
PUBLIC_URL = "https://student-housing-nvaq8qkrfhc4trzuvkgmnc.streamlit.app"

# ✅ Cloudinary (senin bilgiler)
CLOUDINARY_CLOUD_NAME = "dsmcukmw7"
CLOUDINARY_UPLOAD_PRESET = "student_housing_unsigned"

st.set_page_config(page_title="Student Housing", layout="centered")
st.title("🏠 Student Housing")

# --- UI (basit güzelleştirme) ---
st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 980px; }
.card {
  border: 1px solid rgba(49,51,63,0.2);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
  margin-bottom: 12px;
}
.badge {
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(49,51,63,0.2);
  margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)


def upload_to_cloudinary(file_bytes: bytes, filename: str) -> str:
    """
    Unsigned upload (upload preset ile).
    Başarılı olursa secure_url döndürür, hata olursa exception fırlatır.
    """
    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"
    files = {"file": (filename, file_bytes)}
    data = {"upload_preset": CLOUDINARY_UPLOAD_PRESET}

    r = requests.post(url, files=files, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["secure_url"]


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

# ✅ QR kod: herkesin açabileceği PUBLIC URL
st.sidebar.markdown("### 📱 QR Code (Propriétaire)")
owner_url = f"{PUBLIC_URL}/?mode=owner"

qr = qrcode.make(owner_url)
buf = BytesIO()
qr.save(buf, format="PNG")
buf.seek(0)
st.sidebar.image(buf, caption="Scanner pour publier un logement")
st.sidebar.caption(owner_url)


def build_uni_select(unis, label_title: str, key: str):
    """Dropdown’da kullanıcıya güzel label gösterip, id döndürür."""
    label_to_id = {}
    for u in unis:
        arr = u.get("arrondissement")
        label = f"{u.get('nom','')} ({arr})" if arr else u.get("nom", "")
        label_to_id[label] = u.get("id")

    labels = [k for k in label_to_id.keys() if k]
    if not labels:
        st.error("Universities list is empty. Check universities.json")
        st.stop()

    selected_label = st.selectbox(label_title, labels, key=key)
    return label_to_id[selected_label]


# ---------------- OWNER MODE ----------------
if mode == "Propriétaire (QR)":
    st.header("🏷️ Ajouter un logement")
    st.caption("Publiez un logement pour les étudiants")

    unis = get_all_universities()
    universite = build_uni_select(unis, "Université ciblée", key="owner_uni")

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

    # ✅ FOTOĞRAF (dosya seç + cloudinary) + URL fallback
    st.subheader("🖼️ Photo du logement")

    uploaded_file = st.file_uploader(
        "Choisir une photo (png/jpg/jpeg)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False
    )

    image_url_manual = st.text_input(
        "ou Photo URL (optionnel)",
        placeholder="https://..."
    )

    st.caption("💡 Dosya seçersen otomatik Cloudinary'ye yüklenir. İstersen direkt URL de yapıştırabilirsin.")

    st.divider()

    # ✅ Konum (harita için)
    st.subheader("📍 Localisation (optionnel)")
    st.caption("Google Maps’ten konumu açıp latitude/longitude değerlerini buraya yapıştırabilirsin.")

    add_location = st.checkbox("Konum eklemek istiyorum", value=False)
    if add_location:
        colx, coly = st.columns(2)
        with colx:
            latitude = st.number_input("Latitude", value=48.8566, format="%.6f")
        with coly:
            longitude = st.number_input("Longitude", value=2.3522, format="%.6f")
    else:
        latitude = None
        longitude = None

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
            st.stop()
        if loyer_max < loyer_min:
            st.error("❌ Le loyer maximum doit être ≥ au loyer minimum.")
            st.stop()

        # ✅ final image url (öncelik: upload -> url input)
        final_image_url = (image_url_manual or "").strip()

        if uploaded_file is not None:
            try:
                with st.spinner("📤 Photo Cloudinary'ye yükleniyor..."):
                    final_image_url = upload_to_cloudinary(
                        uploaded_file.getvalue(),
                        uploaded_file.name
                    )
                st.success("✅ Photo upload OK")
            except Exception as e:
                st.warning(f"⚠️ Upload échoué: {e}")
                st.info("İstersen Photo URL alanına direkt bir link yapıştırabilirsin.")

        created = add_listing({
            "universite": universite,
            "nom": nom.strip(),
            "distance_km": float(distance_km),

            "loyer_min": int(loyer_min),
            "loyer_max": int(loyer_max),
            "type": type_logement,
            "meubles": bool(meubles),
            "charges_incluses": bool(charges_incluses),

            "image_url": final_image_url,  # ✅ KAYDEDİLEN FOTO URL

            # ✅ map (checkbox ile)
            "latitude": float(latitude) if latitude is not None else None,
            "longitude": float(longitude) if longitude is not None else None,

            "proprietaire": proprietaire.strip(),
            "telephone": contact_tel.strip(),
            "email": contact_email.strip(),
            "contact_pref": contact_pref,
            "whatsapp": whatsapp.strip(),

            "quartier": adresse_quartier.strip(),
            "disponible": str(disponible),
            "description": (description or "").strip(),
            "regles": regles,
        })

        st.success(f"✅ Logement ajouté ! (id = {created['id']})")
        st.info("Passe en mode Étudiant pour le voir apparaître.")

    st.stop()


# ---------------- ÉTUDIANT MODE ----------------
unis = get_all_universities()
uni_id = build_uni_select(unis, "Choisis ton université", key="student_uni")

st.subheader("🔎 Filtres")
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

colC, colD = st.columns(2)
with colC:
    only_meuble = st.checkbox("Seulement meublé")
with colD:
    only_charges = st.checkbox("Charges incluses")

sort_by = st.selectbox("Trier par", ["Distance", "Prix (min)", "Prix (max)"])

matches = get_matches(uni_id, max_km=max_km) or []


def listing_budget_ok(l):
    if budget_max < budget_min:
        return False

    if "loyer" in l:
        val = int(l["loyer"])
        return budget_min <= val <= budget_max

    lo_min = int(l.get("loyer_min", 0))
    lo_max = int(l.get("loyer_max", lo_min))
    return not (lo_max < budget_min or lo_min > budget_max)


def listing_type_ok(l):
    if not types_filter:
        return True
    return l.get("type") in types_filter or l.get("type_logement") in types_filter


def listing_flags_ok(l):
    if only_meuble and not l.get("meubles"):
        return False
    if only_charges and not l.get("charges_incluses"):
        return False
    return True


filtered = [l for l in matches if listing_budget_ok(l) and listing_type_ok(l) and listing_flags_ok(l)]


def price_min(l):
    return int(l.get("loyer", l.get("loyer_min", 10**9)))


def price_max(l):
    return int(l.get("loyer", l.get("loyer_max", 10**9)))


if sort_by == "Distance":
    filtered.sort(key=lambda x: float(x.get("distance_km", 10**9)))
elif sort_by == "Prix (min)":
    filtered.sort(key=price_min)
else:
    filtered.sort(key=price_max)


# ✅ Harita (varsa)
map_points = []
for l in filtered:
    if l.get("latitude") is not None and l.get("longitude") is not None:
        map_points.append({"lat": float(l["latitude"]), "lon": float(l["longitude"])})

if map_points:
    st.subheader("🗺️ Carte")
    df = pd.DataFrame(map_points)
    st.map(df)

st.subheader("Résultats")
if not filtered:
    st.info("Aucun logement trouvé.")
else:
    for l in filtered:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Fotoğraf
        if l.get("image_url"):
            try:
                st.image(l["image_url"], use_container_width=True)
            except Exception:
                st.caption("📷 Image non disponible")

        st.markdown(f"### {l.get('nom', '')}")
        st.markdown(
            f"""
<span class="badge">📍 {l.get('distance_km', '?')} km</span>
<span class="badge">🛏️ {l.get('type', '')}</span>
""",
            unsafe_allow_html=True
        )

        if "loyer" in l:
            st.write(f"💶 {l['loyer']} €")
        else:
            st.write(f"💶 {l.get('loyer_min', '?')}–{l.get('loyer_max', '?')} €")

        if l.get("meubles"):
            st.write("🪑 Meublé")
        if l.get("charges_incluses"):
            st.write("⚡ Charges incluses")
        if l.get("quartier"):
            st.write(f"📌 {l['quartier']}")
        if l.get("disponible"):
            st.write(f"📅 Disponible: {l['disponible']}")
        if l.get("description"):
            st.caption(l["description"])

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

        st.markdown("</div>", unsafe_allow_html=True)
