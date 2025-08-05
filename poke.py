import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_KEY = os.getenv("POKETCG_API_KEY")
headers = {"X-Api-Key": API_KEY} if API_KEY else {}

st.title("Julubo‑Pokémon Prijstracker")

# Sets ophalen
resp = requests.get("https://api.pokemontcg.io/v2/sets", headers=headers)
sets = resp.json().get("data", [])
set_opts = {s["name"]: s["id"] for s in sets}

set_choice = st.selectbox("Kies kaartset", list(set_opts.keys()))
card_name = st.text_input("Zoek kaart (naam)")

if st.button("Haal kaartdata"):
    params = {"q": f"set.id:{set_opts[set_choice]} name:{card_name}"}
    resp2 = requests.get("https://api.pokemontcg.io/v2/cards", params=params, headers=headers)
    data = resp2.json().get("data", [])
    if data:
        card = data[0]
        st.image(card["images"]["small"])
        st.write(card["name"], card["set"]["name"])
        prices = card.get("tcgplayer", {}).get("prices") or card.get("tcgplayer", {})
        st.write("Huidige prijs:", prices)
        # Historische data uit eigen CSV/database ophalen
        df = pd.read_csv("price_history.csv")
        df_card = df[(df["card_id"] == card["id"])]
        if not df_card.empty:
            fig = px.line(df_card, x="date", y="price", title=f"Prijsverloop – {card['name']}")
            st.plotly_chart(fig)
    else:
        st.error("Kaart niet gevonden.")
