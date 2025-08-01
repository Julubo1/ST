import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from PIL import Image

st.set_page_config(page_title="Julubo Analyse", layout="wide")
st.title("📊 Julubo Automatische Data-analyse")

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

# --- Upload sectie
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

    # --- Tabs voor analyse
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

    with tab2:
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        if not numeric_cols:
            st.warning("Geen numerieke kolommen gevonden voor grafieken.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                selected_col = st.selectbox("📊 Kolom voor histogram", numeric_cols)
                fig, ax = plt.subplots()
                sns.histplot(df[selected_col].dropna(), kde=True, ax=ax)
                ax.set_title(f"Verdeling van {selected_col}")
                st.pyplot(fig)

            with col2:
                if len(numeric_cols) > 1:
                    x = st.selectbox("🟦 X-as", numeric_cols, index=0, key="x")
                    y = st.selectbox("🟥 Y-as", numeric_cols, index=1, key="y")
                    fig2, ax2 = plt.subplots()
                    sns.scatterplot(data=df, x=x, y=y, ax=ax2)
                    ax2.set_title(f"Relatie: {x} vs {y}")
                    st.pyplot(fig2)

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
