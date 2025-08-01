import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
from PIL import Image

st.set_page_config(page_title="Julubo Analyse", layout="wide")

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.logo-container {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}
.logo-container img {
    height: 60px;
    margin-right: 15px;
}
</style>
<div class="logo-container">
    <img src="https://julubo.nl/media/website/Logo-Julubo-2-2.png" alt="Julubo Logo">
    <h2>Julubo Automatische Analyse</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Upload een Excel- of CSV-bestand. Julubo analyseert automatisch de inhoud van je dataset 
en genereert inzichten, visualisaties en een downloadbaar rapport.
""")

uploaded_file = st.file_uploader("📁 Upload Excel of CSV", type=["xlsx", "csv"])

@st.cache_data

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if uploaded_file:
    try:
        df = load_data(uploaded_file)
    except Exception as e:
        st.error(f"❌ Kon bestand niet inlezen: {e}")
        st.stop()

    st.success("✅ Bestand succesvol geladen!")
    st.dataframe(df.head(10), use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["📌 Samenvatting", "📈 Grafieken", "📥 Download"])

    with tab1:
        st.subheader("🔎 Statistische samenvatting")
        st.write(df.describe(include='all').transpose())

        st.subheader("🧠 Detected kolomtypes")
        dtypes = pd.DataFrame({
            "Kolom": df.columns,
            "Type": df.dtypes.astype(str),
            "Unieke waarden": df.nunique(),
            "Null-waarden": df.isnull().sum()
        })
        st.dataframe(dtypes)

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        st.subheader("🚨 Waarschuwingsdetectie (Outliers)")
        warnings = []
        for col in numeric_cols:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            if (z_scores > 3).sum() > 0:
                warnings.append(f"⚠️ {col}: bevat {int((z_scores > 3).sum())} mogelijke uitschieters (Z-score > 3)")
        if warnings:
            for w in warnings:
                st.write(w)
        else:
            st.success("Geen opvallende uitschieters gevonden in numerieke kolommen.")

        st.subheader("📊 Correlatie tussen numerieke kolommen")
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            fig_corr, ax_corr = plt.subplots(figsize=(10, 6))
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=ax_corr)
            st.pyplot(fig_corr)

        st.subheader("📑 Geautomatiseerde observaties")
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            st.write(f"Kolom **{col}** heeft een gemiddelde van **{mean:.2f}** en standaarddeviatie van **{std:.2f}**.")
            if df[col].isnull().sum() > 0:
                st.warning(f"{df[col].isnull().sum()} ontbrekende waarden in {col}.")

        st.subheader("🧪 Dataconsistentie & Duplicaten")
        st.write(f"Totaal rijen: {len(df)}")
        dupes = df.duplicated().sum()
        if dupes:
            st.warning(f"Bevat {dupes} duplicaten.")
        else:
            st.success("Geen duplicaten gevonden.")

        if datetime_cols:
            st.subheader("📈 Tijdreeksanalyse")
            dt_col = st.selectbox("Datumkolom kiezen", datetime_cols)
            metric = st.selectbox("Numerieke kolom voor tijdreeks", numeric_cols)
            df[dt_col] = pd.to_datetime(df[dt_col])
            time_df = df[[dt_col, metric]].dropna().sort_values(dt_col)
            time_df = time_df.groupby(pd.Grouper(key=dt_col, freq='W'))[metric].mean()
            st.line_chart(time_df)

    with tab2:
        st.subheader("📈 Verken je data via grafieken")
        plot_type = st.radio("Kies plottype:", ["Histogram (numeriek)", "Scatterplot", "Frequentieplot (categorisch)"])

        if plot_type == "Histogram (numeriek)":
            if numeric_cols:
                selected_col = st.selectbox("Kolom voor histogram", numeric_cols)
                fig, ax = plt.subplots()
                sns.histplot(df[selected_col].dropna(), kde=True, ax=ax)
                ax.set_title(f"Verdeling van {selected_col}")
                st.pyplot(fig)
            else:
                st.warning("Geen numerieke kolommen beschikbaar.")

        elif plot_type == "Scatterplot":
            if len(numeric_cols) >= 2:
                x = st.selectbox("X-as", numeric_cols, index=0)
                y = st.selectbox("Y-as", numeric_cols, index=1)
                fig2, ax2 = plt.subplots()
                sns.scatterplot(data=df, x=x, y=y, ax=ax2)
                ax2.set_title(f"Relatie tussen {x} en {y}")
                st.pyplot(fig2)
            else:
                st.warning("Minimaal twee numerieke kolommen nodig voor een scatterplot.")

        elif plot_type == "Frequentieplot (categorisch)":
            if category_cols:
                cat_col = st.selectbox("Kolom voor frequentieplot", category_cols)
                fig3, ax3 = plt.subplots()
                sns.countplot(data=df, x=cat_col, order=df[cat_col].value_counts().index[:15], ax=ax3)
                ax3.set_title(f"Frequentie van {cat_col}")
                ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45, ha='right')
                st.pyplot(fig3)
            else:
                st.warning("Geen categorische kolommen beschikbaar.")

    with tab3:
        st.subheader("📥 Download analyse & gegevens")
        summary = df.describe().transpose()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Gegevens")
            summary.to_excel(writer, sheet_name="Analyse")
        st.download_button(
            "📤 Download Excel-bestand",
            data=output.getvalue(),
            file_name="julubo_rapport.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("⬆️ Upload een bestand om te starten.")
