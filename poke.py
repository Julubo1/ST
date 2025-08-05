import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

### TESTIG TESTINGNG
#### TETETET
##TETEE
# API-key ophalen
API_KEY = st.secrets["POKETCG_API_KEY"]

headers = {"X-Api-Key": API_KEY}
st.write("API key loaded:", bool(API_KEY))

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
        r = requests.get("https://api.pokemontcg.io/v2/sets", headers=HEADERS)
        r.raise_for_status()
        return r.json().get("data", [])
    except:
        return []

@st.cache_data(ttl=600)
def search_card(set_id, card_name):
    q = f"set.id:{set_id} name:{card_name}"
    try:
        r = requests.get("https://api.pokemontcg.io/v2/cards", headers=HEADERS, params={"q": q})
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

# ========== UI ==========

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

    with st.spinner("Kaartdata ophalen..."):
        cards = search_card(set_opts[set_choice], card_name)

    if not cards:
        st.error("Geen kaart gevonden met deze naam in de gekozen set.")
        st.stop()

    card = cards[0]
    st.image(card["images"]["small"])
    st.subheader(card["name"])
    st.caption(f"Set: {card['set']['name']}")

    prices = card.get("tcgplayer", {}).get("prices") or card.get("tcgplayer", {})
    if prices:
        st.write("💰 Huidige prijsinformatie:")
        st.json(prices)
    else:
        st.warning("Geen prijsinformatie beschikbaar.")

    df_card = load_price_history(card["id"])
    if not df_card.empty:
        fig = px.line(df_card, x="date", y="price", title=f"Prijsverloop – {card['name']}")
        st.plotly_chart(fig)
    else:
        st.info("Geen historische prijsdata beschikbaar voor deze kaart.")
