import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Painel IDHM Pernambuco - Polos de Desenvolvimento", layout="wide")

st.title("📊 Painel Interativo – Polos de Desenvolvimento e Cidades Vizinhas em PE")
st.markdown("Este painel permite identificar municípios com alto IDHM (potenciais polos de desenvolvimento) e visualizar cidades próximas com IDHM mais baixo, que podem se beneficiar de investimentos e parcerias.")

uploaded_file = st.file_uploader("📂 Envie o arquivo CSV com as colunas: Municipio, Idhm, Latitude, Longitude", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors='coerce')
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors='coerce')
    df["Idhm"] = pd.to_numeric(df["Idhm"], errors='coerce')
    df.dropna(subset=["Idhm", "Latitude", "Longitude"], inplace=True)
else:
    st.warning("Por favor, envie um arquivo CSV para continuar.")
    st.stop()

# === Tabs ===
tab1, tab2, tab3 = st.tabs(["📈 Visão Geral do IDHM", "🗺️ Mapa Geral de IDHM", "🏭 Polos e Potenciais Vizinhanças"])

# === TAB 1: VISÃO GERAL ===
with tab1:
    st.subheader("📊 Distribuição do IDHM em Pernambuco")
    st.dataframe(df[["Municipio", "Idhm", "Latitude", "Longitude"]].sort_values("Idhm", ascending=False).head(20))

    fig_bar = px.bar(df.sort_values("Idhm", ascending=False).head(15),
                     x="Municipio", y="Idhm",
                     title="Top 15 Municípios com Maior IDHM em Pernambuco",
                     color="Idhm", color_continuous_scale="Viridis")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Estatísticas Gerais do IDHM")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Média do IDHM", f"{df['Idhm'].mean():.3f}")
    with col2:
        st.metric("Maior IDHM", f"{df['Idhm'].max():.3f}")
    with col3:
        st.metric("Menor IDHM", f"{df['Idhm'].min():.3f}")

# === TAB 2: MAPA GERAL ===
with tab2:
    st.subheader("🗺️ Mapa Interativo do IDHM dos Municípios de Pernambuco")
    st.markdown("Explore a distribuição do IDHM em Pernambuco. O tamanho e a cor dos círculos indicam o valor do IDHM.")

    view_state_general = pdk.ViewState(
        latitude=df["Latitude"].mean(),
        longitude=df["Longitude"].mean(),
        zoom=6,
        pitch=45,
    )

    def get_color_from_idhm(idhm_val):
        min_idhm_norm = df["Idhm"].min()
        max_idhm_norm = df["Idhm"].max()
        if max_idhm_norm == min_idhm_norm:
            normalized_idhm = 0.5
        else:
            normalized_idhm = (idhm_val - min_idhm_norm) / (max_idhm_norm - min_idhm_norm)

        # Gradiente do vermelho (baixo) ao verde (alto)
        r = int(255 * (1 - normalized_idhm))
        g = int(255 * normalized_idhm)
        b = 0
        return [r, g, b, 180]

    df["color_idhm"] = df["Idhm"].apply(get_color_from_idhm)

    # Mapa interativo com tooltip aprimorado
    layer_general = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[Longitude, Latitude]",
        get_color="color_idhm",
        get_radius="Idhm * 6000",
        pickable=True,
        auto_highlight=True,
        tooltip={
            "html": """
                <div style='font-family:Arial; font-size:13px'>
                    <b>🏙️ Município:</b> {Municipio}<br>
                    <b>📊 IDHM:</b> <span style='color:yellow'>{Idhm:.3f}</span><br>
                    <b>🌍 Latitude:</b> {Latitude:.4f}<br>
                    <b>🌍 Longitude:</b> {Longitude:.4f}
                </div>
            """,
            "style": {"backgroundColor": "rgba(0,0,0,0.7)", "color": "white", "border-radius": "5px", "padding": "8px"}
        }
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state_general,
        layers=[layer_general],
    ))

    # Legenda mais visual
    st.markdown("""
    ### 🔎 Interpretação do mapa
    - **Cores**:
        - 🟥 Vermelho → IDHM **baixo** (≈ 0.5)
        - 🟨 Amarelo → IDHM **médio** (≈ 0.65)
        - 🟩 Verde → IDHM **alto** (≈ 0.75 ou mais)
    - **Tamanho dos círculos**: proporcional ao valor do IDHM.
    - **Dica**: Passe o mouse sobre um município para ver seu IDHM exato e coordenadas.
    """)

# === TAB 3: POLOS DE DESENVOLVIMENTO ===
with tab3:
    st.subheader("🏭 Análise de Polos de Desenvolvimento e Cidades Vizinhas")
    st.markdown("Selecione um município com IDHM alto para identificar cidades próximas com IDHM mais baixo, que podem ser alvos de estratégias de desenvolvimento regional.")

    df_high_idhm = df[df["Idhm"] >= df["Idhm"].mean()].sort_values("Idhm", ascending=False)
    
    if not df_high_idhm.empty:
        municipio_ref_name = st.selectbox(
            "1. Selecione um município com IDHM alto (Polo de Desenvolvimento):",
            df_high_idhm["Municipio"].unique()
        )

        muni_base = df[df["Municipio"] == municipio_ref_name].iloc[0]
        lat_ref, lon_ref, idhm_ref = muni_base["Latitude"], muni_base["Longitude"], muni_base["Idhm"]

        st.write(f"**Polo Selecionado:** {municipio_ref_name} (IDHM: {idhm_ref:.3f})")

        raio = st.slider("2. Raio de busca para cidades próximas (km):", 10, 200, 50)
        min_idhm_proximo = st.slider("3. IDHM Mínimo para cidades próximas (excluir polos muito baixos):", 0.4, 0.7, 0.55, 0.01)
        max_idhm_proximo = st.slider("4. IDHM Máximo para cidades próximas (focar em cidades com IDHM médio/baixo):", 0.5, 0.8, 0.65, 0.01)

        # Função de cálculo de distância Haversine (aproximada, sem geopy)
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Raio da Terra em km
            lat1_rad = np.radians(lat1)
            lon1_rad = np.radians(lon1)
            lat2_rad = np.radians(lat2)
            lon2_rad = np.radians(lon2)

            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad

            a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

            distance = R * c
            return distance

        df["Distancia_km"] = df.apply(lambda x: haversine_distance(lat_ref, lon_ref, x["Latitude"], x["Longitude"]), axis=1)
        
        proximos = df[
            (df["Distancia_km"] <= raio) &
            (df["Municipio"] != municipio_ref_name) &
            (df["Idhm"] < idhm_ref) &
            (df["Idhm"] >= min_idhm_proximo) &
            (df["Idhm"] <= max_idhm_proximo)
        ].sort_values("Idhm", ascending=True)

        if not proximos.empty:
            st.write(f"Municípios próximos de **{municipio_ref_name}** (dentro de {raio} km) com IDHM entre {min_idhm_proximo:.2f} e {max_idhm_proximo:.2f} (potenciais para desenvolvimento):")
            st.dataframe(proximos[["Municipio", "Idhm", "Distancia_km"]].round(3))

            polo_df = pd.DataFrame([{
                'Municipio': muni_base['Municipio'],
                'Latitude': muni_base['Latitude'],
                'Longitude': muni_base['Longitude'],
                'Idhm': muni_base['Idhm'],
                'color_idhm': [255, 0, 0, 200], # Vermelho para o polo
                'Distancia_km': 0
            }])
            
            proximos['color_idhm'] = proximos['Idhm'].apply(get_color_from_idhm)
            
            map_data_polos = pd.concat([polo_df, proximos])

            if not map_data_polos.empty:
                center_lat = map_data_polos["Latitude"].mean()
                center_lon = map_data_polos["Longitude"].mean()
                
                max_dist = map_data_polos["Distancia_km"].max()
                zoom_level = 6
                if max_dist > 0:
                    if max_dist < 20: zoom_level = 10
                    elif max_dist < 50: zoom_level = 9
                    elif max_dist < 100: zoom_level = 8
                    elif max_dist < 150: zoom_level = 7
                    elif max_dist < 200: zoom_level = 6

                initial_view_state_polos = pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=zoom_level,
                    pitch=45,
                )

                layer_polos = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_data_polos,
                    get_position="[Longitude, Latitude]",
                    get_color="color_idhm",
                    get_radius="Idhm * 5000",
                    pickable=True,
                    auto_highlight=True,
                    tooltip={
                        "html": "<b>Município:</b> {Municipio}<br><b>IDHM:</b> {Idhm:.3f}<br><b>Distância:</b> {Distancia_km:.2f} km",
                        "style": {"backgroundColor": "steelblue", "color": "white"}
                    }
                )

                st.pydeck_chart(pdk.Deck(
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state=initial_view_state_polos,
                    layers=[layer_polos],
                ))
                st.caption("O círculo vermelho representa o polo de desenvolvimento selecionado. Os círculos coloridos representam as cidades próximas, com cores mais verdes indicando IDHM mais alto e tamanhos proporcionais ao IDHM.")
            else:
                st.info("Nenhum município próximo encontrado com os critérios selecionados para visualização no mapa.")
        else:
            st.info("Nenhum município próximo encontrado com os critérios selecionados.")
    else:
        st.warning("Não há municípios com IDHM acima da média para selecionar como polo. Verifique seus dados.")
st.markdown("---")
st.markdown(
    "📖 **Fonte:** [IBGE - Recife, PE](https://www.ibge.gov.br/cidades-e-estados/pe/recife.html)"
)