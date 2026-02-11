import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================

st.set_page_config(page_title="Inspeção de Escadas", layout="wide")

st.title("🪜 Sistema de Inspeção de Escadas")

# Criar pasta fotos automaticamente se não existir
if not os.path.exists("fotos"):
    os.makedirs("fotos")

# Arquivo banco de dados
ARQUIVO = "dados_escadas.csv"

# Criar CSV se não existir
if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=[
        "ID", "Data", "Responsavel", "Setor",
        "Condicao", "Observacao", "Foto"
    ])
    df.to_csv(ARQUIVO, index=False)

# ===============================
# MENU
# ===============================

menu = st.sidebar.selectbox(
    "Menu",
    ["Nova Inspeção", "Consultar Escada"]
)

# ===============================
# NOVA INSPEÇÃO
# ===============================

if menu == "Nova Inspeção":

    st.subheader("📋 Registrar Nova Inspeção")

    with st.form("form_inspecao"):

        id_escada = st.text_input("ID da Escada")
        responsavel = st.text_input("Responsável")
        setor = st.text_input("Setor")

        condicao = st.selectbox(
            "Condição",
            ["Boa", "Regular", "Ruim"]
        )

        observacao = st.text_area("Observações")

        foto = st.file_uploader("📷 Upload da Foto", type=["jpg", "png", "jpeg"])

        enviar = st.form_submit_button("Salvar Inspeção")

    if enviar:

        if id_escada == "":
            st.error("Informe o ID da escada.")
        else:

            nome_foto = ""

            # Salvar foto
            if foto is not None:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                nome_foto = f"{id_escada}_{timestamp}.jpg"
                caminho = os.path.join("fotos", nome_foto)

                with open(caminho, "wb") as f:
                    f.write(foto.getbuffer())

            nova_linha = pd.DataFrame([{
                "ID": id_escada,
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Responsavel": responsavel,
                "Setor": setor,
                "Condicao": condicao,
                "Observacao": observacao,
                "Foto": nome_foto
            }])

            df = pd.read_csv(ARQUIVO)
            df = pd.concat([df, nova_linha], ignore_index=True)
            df.to_csv(ARQUIVO, index=False)

            st.success("✅ Inspeção salva com sucesso!")

# ===============================
# CONSULTAR ESCADA
# ===============================

elif menu == "Consultar Escada":

    st.subheader("🔎 Consultar Escada por ID")

    id_busca = st.text_input("Digite o ID da escada")

    if id_busca:

        df = pd.read_csv(ARQUIVO)

        resultado = df[df["ID"] == id_busca]

        if not resultado.empty:

            st.success("Escada encontrada!")

            st.dataframe(resultado)

            for index, row in resultado.iterrows():

                if row["Foto"] != "":
                    caminho_foto = os.path.join("fotos", row["Foto"])

                    if os.path.exists(caminho_foto):
                        st.image(caminho_foto, caption="Foto da inspeção")
        else:
            st.warning("Escada não encontrada.")
