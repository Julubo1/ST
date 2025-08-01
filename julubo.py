import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

st.set_page_config(page_title="Julubo Auto Analyse", layout="wide")

st.title("Julubo Automatische Data-analyse")

st.markdown("""
Upload je Excel- of CSV-bestand en ontvang direct inzichten op basis van je data.
Julubo analyseert automatisch kolommen, berekent kerncijfers en toont relevante grafieken.
""")

uploaded_file = st.file_uploader("Upload een Excel of CSV bestand", type=["xlsx", "csv"])

if uploaded_file:
    # Bestandsinvoer verwerken
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Fout bij het inlezen van het bestand: {e}")
        st.stop()

    st.success("Bestand succesvol geladen ✅")
    st.write("Voorbeeld van je data:", df.head())

    st.subheader("Statistische samenvatting")
    st.write(df.describe(include='all').transpose())

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols:
        st.subheader("Automatisch gegenereerde grafieken")
        selected_col = st.selectbox("Kies een numerieke kolom voor grafiek", numeric_cols)

        fig, ax = plt.subplots()
        sns.histplot(df[selected_col].dropna(), kde=True, ax=ax)
        ax.set_title(f"Verdeling van {selected_col}")
        st.pyplot(fig)

        st.subheader(" Kolomvergelijking")
        if len(numeric_cols) > 1:
            col_x = st.selectbox("X-as", numeric_cols, index=0)
            col_y = st.selectbox("Y-as", numeric_cols, index=1)

            fig2, ax2 = plt.subplots()
            sns.scatterplot(data=df, x=col_x, y=col_y, ax=ax2)
            ax2.set_title(f"Relatie tussen {col_x} en {col_y}")
            st.pyplot(fig2)

    # Downloadbare output (samenvatting als Excel)
    st.subheader("Download analyse")
    summary = df.describe().transpose()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Gegevens")
        summary.to_excel(writer, sheet_name="Samenvatting")

    st.download_button(
        label="Download Excel-analyse",
        data=output.getvalue(),
        file_name="julubo_analyse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("⏳ Wacht op upload...")
