import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from urllib.parse import quote

# --- Functie: OpenKVK opzoeken ---
def zoek_openkvk(zoekterm):
    url = f"https://api.openkvk.nl/api/v1/companies?search={quote(zoekterm)}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("data", [])
    except:
        return []

# --- Functie: Filteren op branche, land, regio ---
def filter_resultaten(resultaten, branche, land, regio):
    df = pd.DataFrame(resultaten)

    if branche:
        df = df[df["sbi_code_description"].str.contains(branche, case=False, na=False)]

    if land:
        df = df[df["country"].str.contains(land, case=False, na=False)]

    if regio:
        df = df[df["city"].str.contains(regio, case=False, na=False)]

    return df

# --- Functie: Voeg ECD toe via CSV (optioneel) ---
def verrijk_met_ecd(df, ecd_df):
    return df.merge(ecd_df, how="left", left_on="name", right_on="organisatie")

# --- Streamlit UI ---
st.set_page_config(page_title="Open Data Bedrijvenscanner", layout="wide")
st.title("🔎 Open Data Bedrijvenscanner")

st.markdown("Zoek bedrijven op basis van naam, branche, land en/of regio. Combineert OpenKVK met eigen ECD-data.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    naam = st.text_input("🔤 Bedrijfsnaam (deel of volledig)")
with col2:
    branche = st.text_input("🏭 Branche / sector")
with col3:
    land = st.selectbox("🌍 Land", ["", "Nederland"], index=1)
with col4:
    regio = st.text_input("📍 Regio / plaats")

ecd_file = st.file_uploader("📎 Upload optionele ECD-mapping CSV (kolommen: organisatie, ecd_systeem)", type="csv")

zoek_button = st.button("Zoeken")

if zoek_button:
    st.info("Zoeken in OpenKVK...")
    data = zoek_openkvk(naam if naam else branche)

    if not data:
        st.warning("Geen resultaten gevonden.")
    else:
        st.success(f"{len(data)} bedrijven gevonden.")
        df = pd.DataFrame(data)

        # Structureren
        df = df.rename(columns={
            "trade_names": "name",
            "sbi_code": "sbi_code",
            "sbi_code_description": "sbi_code_description",
            "city": "city",
            "address": "address",
            "kvk_number": "kvk_number",
        })
        df["country"] = "Nederland"

        # Filteren
        df = filter_resultaten(df, branche, land, regio)

        # Verrijken met ECD
        if ecd_file:
            ecd_df = pd.read_csv(ecd_file)
            df = verrijk_met_ecd(df, ecd_df)

        st.dataframe(df)

        # Downloadknoppen
        col_csv, col_excel = st.columns(2)
        with col_csv:
            st.download_button("⬇️ Download als CSV", data=df.to_csv(index=False), file_name="bedrijven.csv", mime="text/csv")
        with col_excel:
            towrite = BytesIO()
            df.to_excel(towrite, index=False, engine="openpyxl")
            st.download_button("⬇️ Download als Excel", data=towrite.getvalue(), file_name="bedrijven.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
