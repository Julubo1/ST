import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
from io import BytesIO

# OpenKVK zoeken via overheid.io
def zoek_openkvk(term):
    url = f"https://api.overheid.io/openkvk?query={quote(term)}&size=20&fields[]=handelsnaam&fields[]=postcode&fields[]=plaats"
    r = requests.get(url)
    data = r.json().get("_embedded", {}).get("bedrijf", [])
    rows = []
    for b in data:
        rows.append({
            "naam": b.get("handelsnaam"),
            "postcode": b.get("postcode"),
            "plaats": b.get("plaats"),
            "kvk": b.get("dossiernummer")
        })
    return pd.DataFrame(rows)

# OpenStreetMap Overpass query: healthcare facilities
def zoek_osm(land, regio, branche):
    bbox = ""  # eventueel filter op binnen Nederland via bbox
    q = """
    [out:json][timeout:25];
    area["name"="%s"]->.searchArea;
    node(area.searchArea)[amenity~"clinic|hospital|doctors"];
    out center;
    """ % land
    r = requests.post("http://overpass-api.de/api/interpreter", data={"data": q})
    data = r.json().get("elements", [])
    rows = []
    for e in data:
        rows.append({
            "osm_name": e.get("tags", {}).get("name"),
            "osm_type": e.get("tags", {}).get("amenity"),
            "lat": e.get("lat"),
            "lon": e.get("lon")
        })
    return pd.DataFrame(rows)

# Wikidata SPARQL zoeken op organisatie
def zoek_wikidata(term):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(f"""
    SELECT ?org ?orgLabel ?sitio ?instelling ?plaatsLabel WHERE {{
      ?org rdfs:label "{term}"@nl.
      OPTIONAL {{ ?org wdt:P159 ?plaats. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "nl,en". }}
    }}
    """)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    rows = []
    for b in res["results"]["bindings"]:
        rows.append({
            "wd_name": b["orgLabel"]["value"],
            "wd_plaats": b.get("plaatsLabel", {}).get("value")
        })
    return pd.DataFrame(rows)

# NACE/SBI mapping in CSV
nace_df = pd.DataFrame({
    "sbi_code": ["47.7", "86.10", "62.01"],
    "omschrijving": ["Detailhandel via post/kantoor", "Verpleegzorg", "Software ontwikkeling"]
})

def filter_input(df, naam, branche, land, regio):
    if naam:
        df = df[df.apply(lambda r: naam.lower() in str(r.get("naam","")).lower(), axis=1)]
    if branche:
        df = df[df.apply(lambda r: branche.lower() in str(r.get("sbi_omschrijving","")).lower(), axis=1)]
    if regio:
        df = df[df["plaats"].str.contains(regio, case=False, na=False)]
    return df

st.title("🔍 Open Data Scanner – meervoudige bronnen")

col1, col2, col3, col4 = st.columns(4)
naam = col1.text_input("Naam")
branche = col2.text_input("Branche")
land = col3.selectbox("Land", ["", "Nederland"])
regio = col4.text_input("Regio / plaats")
ecd_file = st.file_uploader("Optionele ECD-mapping CSV", type="csv")
knop = st.button("Zoeken")

if knop:
    st.info("Resultaten verzamelen…")
    df_okvk = zoek_openkvk(naam or branche) if naam or branche else pd.DataFrame()
    df_wd = zoek_wikidata(naam) if naam else pd.DataFrame()
    df_osm = zoek_osm(land or "Nederland", regio, branche) if land else pd.DataFrame()

    # combineer OpenKVK + mapping NACE
    df_okvk["sbi_omschrijving"] = df_okvk["kvk"].map(lambda _: "")
    df_okvk = filter_input(df_okvk, naam, branche, land, regio)
    if ecd_file:
        ecd = pd.read_csv(ecd_file)
        df_okvk = df_okvk.merge(ecd, how="left", left_on="naam", right_on="organisatie")

    st.subheader("OpenKVK resultaten")
    st.dataframe(df_okvk)
    st.subheader("Wikidata resultaten")
    st.dataframe(df_wd)
    st.subheader("OSM health‑facilities")
    st.dataframe(df_osm)

    # download knoppen voor OpenKVK
    csv = df_okvk.to_csv(index=False)
    xlsx = BytesIO(); df_okvk.to_excel(xlsx, index=False, engine="openpyxl")
    st.download_button("Download CSV", csv, "bedrijven.csv", "text/csv")
    st.download_button("Download Excel", xlsx.getvalue(), "bedrijven.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
