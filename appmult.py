import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
from streamlit_qrcode_scanner import qrcode_scanner

# 1. Configuração da Página (Sempre no início)
st.set_page_config(page_title="Portal SST Integrado", layout="wide", page_icon="🛡️")

# --- LINKS DAS PLANILHAS ---
URL_TREINAMENTOS = "https://docs.google.com/spreadsheets/d/1Qlved6PPLPNSyfhaswGDTgvXkWZ8OcsRRm1yGGaUcz0/export?format=csv&gid=0"
URL_ESCADAS = "https://docs.google.com/spreadsheets/d/131wLP89GL5xTfxe8EN3ajgzoSFH2r69WKEromCd6_i0/edit#gid=532538193"

# --- FUNÇÃO TELA 1: TREINAMENTOS ---
def tela_treinamentos():
    st.title("🛡️ Consulta de Treinamentos e Autorizações")
    st.markdown("---")
   
    matricula_input = st.text_input("Digite a matrícula do trabalhador:")
   
    if matricula_input:
        try:
            df = pd.read_csv(URL_TREINAMENTOS)
            # Unificação de matrícula (075835 = 75835)
            df.columns.values[0] = 'Matricula'
            df['Mat_Num'] = pd.to_numeric(df['Matricula'], errors='coerce')
            busca_num = pd.to_numeric(matricula_input, errors='coerce')
           
            resultados = df[df['Mat_Num'] == busca_num]
           
            if not resultados.empty:
                colaborador = resultados.iloc[0]
                hoje = datetime.now()
               
                st.subheader(f"👤 Colaborador: {colaborador['Nome']}")
                st.info(f"**Unidade:** {colaborador['Unidade']} | **Setor:** {colaborador['Setor']}")

                c1, c2 = st.columns(2)
                with c1:
                    datas_t = pd.to_datetime(resultados['Vencimento Treinamento'], dayfirst=True, errors='coerce').dropna()
                    if not datas_t.empty:
                        v_t = datas_t.max()
                        st.success(f"✅ Treinamento: OK ({v_t.strftime('%d/%m/%Y')})") if v_t >= hoje else st.error(f"❌ Treinamento VENCIDO ({v_t.strftime('%d/%m/%Y')})")
               
                with c2:
                    datas_a = pd.to_datetime(resultados['Vencimento ASO'], dayfirst=True, errors='coerce').dropna()
                    if not datas_a.empty:
                        v_a = datas_a.max()
                        st.success(f"✅ ASO: OK ({v_a.strftime('%d/%m/%Y')})") if v_a >= hoje else st.error(f"❌ ASO VENCIDO ({v_a.strftime('%d/%m/%Y')})")

                st.divider()
                nrs = ['NR10', 'NR11 - Ponte Rolante', 'NR11 - Empilhadeira', 'NR12 - Prensa', 'NR12 - Serra', 'NR33', 'NR35']
                autorizados = [n for n in nrs if n in df.columns and resultados[n].astype(str).str.strip().str.lower().eq('sim').any()]
               
                st.markdown("### ✅ Autorizações Consolidadas")
                if autorizados:
                    cols = st.columns(3)
                    for i, a in enumerate(autorizados):
                        cols[i % 3].write(f"✔️ {a}")
               
                obs = resultados['Observação'].dropna().unique()
                if len(obs) > 0:
                    st.warning(f"📝 **Observações:** {', '.join(obs)}")
            else:
                st.error("Matrícula não encontrada.")
        except Exception as e:
            st.error(f"Erro: {e}")

# --- FUNÇÃO TELA 2: ESCADAS ---
def tela_escadas():
    st.title("📋 Painel de Controle de Escadas")
    st.markdown("---")
   
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_escadas = conn.read(spreadsheet=URL_ESCADAS, ttl=0)
        df_escadas.columns = df_escadas.columns.str.strip()

        with st.expander("🔍 Consultar Escada", expanded=True):
            aba_qr, aba_id = st.tabs(["📷 QR Code", "⌨️ Digitar ID"])
            id_busca = None
            with aba_qr:
                qr = qrcode_scanner(key='scanner_escada')
                if qr: id_busca = str(qr).strip().lstrip('0')
            with aba_id:
                id_m = st.text_input("ID da Escada:")
                if id_m: id_busca = str(id_m).strip().lstrip('0')

        if id_busca:
            df_escadas["ID_AUX"] = df_escadas["Número de Identificação"].astype(str).str.strip().str.lstrip('0')
            res = df_escadas[df_escadas["ID_AUX"] == id_busca]
           
            if not res.empty:
                ultima = res.iloc[-1]
                data_inspecao = pd.to_datetime(ultima["Carimbo de data/hora"], dayfirst=True)
                proxima = data_inspecao + timedelta(days=365)
               
                st.metric("Status da Inspeção", ultima["Status da Inspeção"])
                if datetime.now() > proxima:
                    st.error(f"🚨 INSPEÇÃO VENCIDA EM {proxima.strftime('%d/%m/%Y')}!")
                else:
                    st.info(f"📅 Validade até: {proxima.strftime('%d/%m/%Y')}")
               
                st.dataframe(res.tail(3)) # Mostra as últimas 3 inspeções
            else:
                st.error("Escada não encontrada.")
    except Exception as e:
        st.error(f"Erro ao carregar escadas: {e}")

# --- MENU LATERAL (A MÁGICA ACONTECE AQUI) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/939/939268.png", width=100)
st.sidebar.title("Navegação")
opcao = st.sidebar.radio("Selecione a Ferramenta:", ["👤 Treinamentos", "🪜 Gestão de Escadas"])

st.sidebar.divider()
st.sidebar.markdown("### 🔗 Links Úteis")
st.sidebar.link_button("📝 Nova Inspeção de Escada", "https://docs.google.com/forms/d/...")

# --- ROTEADOR ---
if opcao == "👤 Treinamentos":
    tela_treinamentos()
elif opcao == "🪜 Gestão de Escadas":
    tela_escadas()

