import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

# API-key ophalen
API_KEY = st.secrets["POKETCG_API_KEY"]
headers = {"X-Api-Key": API_KEY}

# ========== Wisselkoers ophalen ==========
@st.cache_data(ttl=3600)
def get_usd_to_eur_rate():
    try:
        r = requests.get("https://api.exchangerate.host/latest", params={"base": "USD", "symbols": "EUR"})
        r.raise_for_status()
        data = r.json()
        rate = data.get("rates", {}).get("EUR")
        if rate is None:
            raise ValueError("EUR rate not found")
        return float(rate)
    except Exception as e:
        # fallback vaste koers
        return 0.92

# ========== STYLING ==========
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.logo-container {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    gap: 15px;
}
.logo-container img {
    height: 60px;
}
</style>
<div class="logo-container">
    <img src="https://julubo.nl/media/website/Logo-Julubo-2-2.png" alt="Julubo Logo">
    <h2>Julubo Pokémon Prijstracker</h2>
</div>
""", unsafe_allow_html=True)

# ========== FUNCTIES ==========

@st.cache_data(ttl=3600)
def get_sets():
    try:
        r = requests.get("https://api.pokemontcg.io/v2/sets", headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])
    except:
        return []

@st.cache_data(ttl=600)
def search_card(set_id, card_name):
    q = f"set.id:{set_id} name:{card_name}"
    try:
        r = requests.get("https://api.pokemontcg.io/v2/cards", headers=headers, params={"q": q})
        r.raise_for_status()
        return r.json().get("data", [])
    except:
        return []

def load_price_history(card_id):
    try:
        df = pd.read_csv("price_history.csv")
        return df[df["card_id"] == card_id]
    except:
        return pd.DataFrame()

def prices_to_eur(prices_usd_dict, usd_to_eur):
    """
    Zet een dict met prijsinformatie in USD om naar EUR,
    teruggegeven als een vergelijkbare dict met EUR-prijzen.
    Verwacht structuur met keys als 'normal', 'holofoil', etc.
    """
    prices_eur = {}
    for key, val in prices_usd_dict.items():
        if isinstance(val, dict) and "market" in val:
            try:
                prices_eur[key] = {"market": round(val["market"] * usd_to_eur, 2)}
            except:
                prices_eur[key] = {"market": None}
        else:
            prices_eur[key] = val  # fallback
    return prices_eur

# ========== UI ==========

usd_to_eur = get_usd_to_eur_rate()

sets = get_sets()
if not sets:
    st.error("Kon geen kaartsets laden. Controleer je internetverbinding of API-key.")
    st.stop()

set_opts = {s["name"]: s["id"] for s in sets}
set_choice = st.selectbox("Kies kaartset", list(set_opts.keys()))
card_name = st.text_input("Zoek kaart op naam")

if st.button("Haal kaartdata"):
    if not card_name.strip():
        st.warning("Voer een kaartnaam in.")
        st.stop()

    with st.spinner("Kaarten ophalen..."):
        cards = search_card(set_opts[set_choice], card_name)

    if not cards:
        st.error("Geen kaart gevonden met deze naam in de gekozen set.")
        st.stop()

    # Maak een dict met kaartnaam + setnaam, markeer 1st Edition kaarten
    card_options = {}
    for c in cards:
        name = c["name"]
        set_name = c["set"]["name"]
        is_1st_ed = ("1st edition" in set_name.lower()) or ("1st edition" in name.lower())
        label = f"{name} ({set_name})"
        if is_1st_ed:
            label += " [1st Edition]"
        card_options[label] = c

    selected_label = st.selectbox("Selecteer kaart (inclusief 1st Edition indien beschikbaar)", list(card_options.keys()))
    card = card_options[selected_label]

    st.image(card["images"]["small"])
    st.subheader(card["name"])
    st.caption(f"Set: {card['set']['name']}")

    prices_usd = card.get("tcgplayer", {}).get("prices") or card.get("tcgplayer", {})
    if prices_usd:
        st.write(f"### Huidige prijsinformatie (wisselkoers USD→EUR: {usd_to_eur:.4f})")
        st.write("**In USD:**")
        st.json(prices_usd)

        prices_eur = prices_to_eur(prices_usd, usd_to_eur)
        st.write("**Omgezet naar EUR:**")
        st.json(prices_eur)
    else:
        st.warning("Geen prijsinformatie beschikbaar.")

    df_card = load_price_history(card["id"])
    if not df_card.empty:
        fig = px.line(df_card, x="date", y="price", title=f"Prijsverloop – {card['name']}")
        st.plotly_chart(fig)
    else:
        st.info("Geen historische prijsdata beschikbaar voor deze kaart.")
