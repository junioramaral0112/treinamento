import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_qrcode_scanner import qrcode_scanner
import base64

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Portal SST Integrado",
    layout="wide",
    page_icon="🛡️"
)

# =====================================================
# LINKS DAS PLANILHAS
# =====================================================
URL_TREINAMENTOS = "https://docs.google.com/spreadsheets/d/1Qlved6PPLPNSyfhaswGDTgvXkWZ8OcsRRm1yGGaUcz0/export?format=csv&gid=0"

URL_ESCADAS = "https://docs.google.com/spreadsheets/d/131wLP89GL5xTfxe8EN3ajgzoSFH2r69WKEromCd6_i0/export?format=csv&gid=532538193"


# =====================================================
# CONVERSOR DE LINK ONEDRIVE (TREINAMENTOS)
# =====================================================
def obter_link_foto(url_original):
    if pd.isna(url_original) or str(url_original).strip() == "":
        return None

    url = str(url_original).strip()

    if "onedrive" in url or "1drv.ms" in url:
        try:
            b64_url = base64.b64encode(url.encode()).decode().replace('/', '_').replace('+', '-').rstrip('=')
            return f"https://api.onedrive.com/v1.0/shares/u!{b64_url}/root/content"
        except:
            return url

    return url


# =====================================================
# TELA 1 - TREINAMENTOS (NÃO ALTERADA)
# =====================================================
def tela_treinamentos():
    st.header("👤 Consulta de Treinamentos")

    matricula_input = st.text_input("Digite a matrícula:", placeholder="Ex: 075835")

    if matricula_input:
        try:
            df = pd.read_csv(URL_TREINAMENTOS, dtype={1: str})
            df.columns.values[1] = 'Matricula'

            df['Mat_Busca'] = df['Matricula'].astype(str).str.strip().str.lstrip('0')
            busca_limpa = str(matricula_input).strip().lstrip('0')

            resultados = df[df['Mat_Busca'] == busca_limpa].copy()

            if not resultados.empty:
                colaborador_base = resultados.dropna(subset=['Nome']).iloc[-1]
                hoje = datetime.now()

                col_foto, col_info = st.columns([1, 3])

                with col_foto:
                    link_direto = obter_link_foto(colaborador_base.get("Foto"))
                    if link_direto:
                        st.image(link_direto, width=180)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)

                with col_info:
                    st.subheader(f"{colaborador_base['Nome']}")
                    st.write(f"*Unidade:* {colaborador_base['Unidade']} | *Setor:* {colaborador_base['Setor']}")

                    v_aso = pd.to_datetime(colaborador_base['Vencimento ASO'], dayfirst=True, errors='coerce')

                    if pd.notna(v_aso):
                        if v_aso >= hoje:
                            st.success(f"✅ ASO OK: {v_aso.strftime('%d/%m/%Y')}")
                        else:
                            st.error(f"❌ ASO VENCIDO: {v_aso.strftime('%d/%m/%Y')}")

                st.divider()
                st.write("### 📜 Validades de Treinamentos Identificados")

                nrs_para_buscar = ['NR10', 'NR35', 'NR11', 'NR12', 'NR18']
                st_cols = st.columns(3)
                idx_col = 0

                for nr in nrs_para_buscar:
                    if nr in resultados.columns:
                        linha_nr = resultados[resultados[nr].astype(str).str.lower().str.contains('sim')]

                        if not linha_nr.empty:
                            data_v = pd.to_datetime(
                                linha_nr.iloc[-1]['Vencimento Treinamento'],
                                dayfirst=True,
                                errors='coerce'
                            )

                            if pd.notna(data_v):
                                with st_cols[idx_col % 3]:
                                    if data_v >= hoje:
                                        st.success(f"*{nr}*\nVence em: {data_v.strftime('%d/%m/%Y')}")
                                    else:
                                        st.error(f"*{nr}*\nVENCIDO: {data_v.strftime('%d/%m/%Y')}")
                                    idx_col += 1

            else:
                st.error("Matrícula não encontrada.")

        except Exception as e:
            st.error(f"Erro ao processar as linhas da planilha: {e}")


# =====================================================
# TELA 2 - ESCADAS (CORRIGIDA)
# =====================================================
def tela_escadas():
    st.header("🪜 Gestão de Escadas")
    st.info("Utilize o scanner ou digite o ID para consultar a escada.")

    try:
        df_escadas = pd.read_csv(URL_ESCADAS)
        df_escadas.columns = df_escadas.columns.str.strip()

        abas = st.tabs(["📷 Ler QR Code", "🔎 Consulta Manual"])

        # =============================
        # QR CODE
        # =============================
        with abas[0]:
            st.subheader("Scanner de QR Code")

            codigo_lido = qrcode_scanner(key="qr_escada")

            if codigo_lido:
                codigo_lido = str(codigo_lido).strip()

                resultado = df_escadas[
                    df_escadas["Número de Identificação"].astype(str).str.strip() == codigo_lido
                ]

                if not resultado.empty:
                    st.success(f"Escada {codigo_lido} encontrada ✅")
                    st.dataframe(resultado, use_container_width=True)
                else:
                    st.error("Escada não encontrada ❌")

        # =============================
        # CONSULTA MANUAL
        # =============================
        with abas[1]:
            st.subheader("Consulta Manual")

            codigo_manual = st.text_input("Digite o Número de Identificação")

            if codigo_manual:
                codigo_manual = str(codigo_manual).strip()

                resultado = df_escadas[
                    df_escadas["Número de Identificação"].astype(str).str.strip() == codigo_manual
                ]

                if not resultado.empty:
                    st.success(f"Escada {codigo_manual} encontrada ✅")
                    st.dataframe(resultado, use_container_width=True)
                else:
                    st.warning("Nenhum registro encontrado.")

    except Exception as e:
        st.error(f"Erro ao carregar planilha de escadas: {e}")


# =====================================================
# MENU LATERAL (INALTERADO)
# =====================================================
with st.sidebar:
    st.title("🚀 Portal SST")
    opcao = st.radio("Ferramenta:", ["👤 Treinamentos", "🪜 Escadas"])
    st.divider()
    st.link_button(
        "📝 Nova Inspeção (Forms)",
        "https://docs.google.com/forms/d/e/1FAIpQLScyv4M1N9A9v8p6O-n9x_r4_0o-p5W-v7Y-f9-0o-p5W-v7Y/viewform"
    )
    if st.button("🔄 Atualizar Dados"):
        st.rerun()


# =====================================================
# CONTROLE DE TELAS
# =====================================================
if opcao == "👤 Treinamentos":
    tela_treinamentos()
else:
    tela_escadas()
