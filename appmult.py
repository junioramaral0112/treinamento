import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
from streamlit_qrcode_scanner import qrcode_scanner

# 1. Configuração da Página (Responsividade total para Celular/PC)
st.set_page_config(
    page_title="Portal SST Integrado", 
    layout="wide", 
    page_icon="🛡️"
)

# --- LINKS DAS PLANILHAS ---
URL_TREINAMENTOS = "https://docs.google.com/spreadsheets/d/1Qlved6PPLPNSyfhaswGDTgvXkWZ8OcsRRm1yGGaUcz0/export?format=csv&gid=0"
URL_ESCADAS = "https://docs.google.com/spreadsheets/d/131wLP89GL5xTfxe8EN3ajgzoSFH2r69WKEromCd6_i0/edit#gid=532538193"

# --- FUNÇÃO TELA 1: TREINAMENTOS ---
def tela_treinamentos():
    st.header("👤 Consulta de Treinamentos")
    
    matricula_input = st.text_input("Digite a matrícula do trabalhador:", placeholder="Ex: 075835")
    
    if matricula_input:
        try:
            # Carrega a planilha
            df = pd.read_csv(URL_TREINAMENTOS)
            df.columns.values[0] = 'Matricula' 
            
            # Unificação de matrícula (075835 = 75835)
            df['Mat_Num'] = pd.to_numeric(df['Matricula'], errors='coerce')
            busca_num = pd.to_numeric(matricula_input, errors='coerce')
            
            resultados = df[df['Mat_Num'] == busca_num]
            
            if not resultados.empty:
                colaborador = resultados.iloc[0]
                hoje = datetime.now()
                
                st.subheader(f"Colaborador: {colaborador['Nome']}")
                st.caption(f"📍 {colaborador['Unidade']} | {colaborador['Setor']}")

                # Layout em colunas que se ajustam no celular
                c1, c2 = st.columns(2)
                
                with c1:
                    # Trava contra NaT (Datas vazias)
                    datas_t = pd.to_datetime(resultados['Vencimento Treinamento'], dayfirst=True, errors='coerce').dropna()
                    if not datas_t.empty:
                        v_t = datas_t.max()
                        if v_t >= hoje:
                            st.success(f"✅ Treinamento: OK ({v_t.strftime('%d/%m/%Y')})")
                        else:
                            st.error(f"❌ Treinamento VENCIDO ({v_t.strftime('%d/%m/%Y')})")
                    else:
                        st.warning("⚠️ Sem data de Treinamento.")

                with c2:
                    datas_a = pd.to_datetime(resultados['Vencimento ASO'], dayfirst=True, errors='coerce').dropna()
                    if not datas_a.empty:
                        v_a = datas_a.max()
                        if v_a >= hoje:
                            st.success(f"✅ ASO: OK ({v_a.strftime('%d/%m/%Y')})")
                        else:
                            st.error(f"❌ ASO VENCIDO ({v_a.strftime('%d/%m/%Y')})")
                    else:
                        st.warning("⚠️ Sem data de ASO.")

                st.divider()
                
                # Consolidação de todas as NRs encontradas em todas as linhas
                nrs = ['NR10', 'NR11 - Ponte Rolante', 'NR11 - Empilhadeira', 'NR12 - Prensa', 
                       'NR12 - Serra', 'NR12 - Esmiril', 'NR12 - Meia Esquadria', 
                       'Troca Gás Empilhadeira', 'NR33', 'NR35']
                
                autorizados = [n for n in nrs if n in df.columns and resultados[n].astype(str).str.strip().str.lower().eq('sim').any()]
                
                if autorizados:
                    st.write("**Autorizações Identificadas:**")
                    cols_nr = st.columns(2)
                    for i, a in enumerate(autorizados):
                        cols_nr[i % 2].write(f"✔️ {a}")
                
                obs_unicas = resultados['Observação'].dropna().unique()
                if len(obs_unicas) > 0:
                    st.info(f"📝 **Notas:** {'; '.join(obs_unicas)}")
            else:
                st.error("Matrícula não encontrada.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

# --- FUNÇÃO TELA 2: ESCADAS ---
def tela_escadas():
    st.header("🪜 Gestão de Escadas")
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_escadas = conn.read(spreadsheet=URL_ESCADAS, ttl=0)
        df_escadas.columns = df_escadas.columns.str.strip()

        aba_qr, aba_id = st.tabs(["📷 Scanner QR", "⌨️ Digitar ID"])
        id_busca = None
        
        with aba_qr:
            qr = qrcode_scanner(key='scanner_escada')
            if qr: id_busca = str(qr).strip().lstrip('0')
        
        with aba_id:
            id_m = st.text_input("ID da Escada (Ex: 001):")
            if id_m: id_busca = str(id_m).strip().lstrip('0')

        if id_busca:
            df_escadas["ID_AUX"] = df_escadas["Número de Identificação"].astype(str).str.strip().str.lstrip('0')
            res = df_escadas[df_escadas["ID_AUX"] == id_busca]
            
            if not res.empty:
                ultima = res.iloc[-1]
                data_inspecao = pd.to_datetime(ultima["Carimbo de data/hora"], dayfirst=True)
                proxima = data_inspecao + timedelta(days=365)
                
                status = str(ultima.get("Status da Inspeção", "")).strip()
                if "Aprovada" in status:
                    st.success(f"### STATUS: {status}")
                else:
                    st.error(f"### STATUS: {status}")
                
                if datetime.now() > proxima:
                    st.error(f"🚨 INSPEÇÃO VENCIDA EM {proxima.strftime('%d/%m/%Y')}")
                else:
                    st.info(f"📅 Validade até: {proxima.strftime('%d/%m/%Y')}")
            else:
                st.error("Escada não encontrada.")
    except Exception as e:
        st.error(f"Erro no sistema de escadas: {e}")

# --- MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    # IMAGEM LOCAL PARA TESTE
    try:
        caminho_logo = r"C:\Users\dilceu.junior\Desktop\sipat_painel\logo_empresa.png"
        st.image(caminho_logo, use_container_width=True)
    except:
        st.warning("⚠️ Logo não encontrado.")
        
    st.title("🚀 Portal SST")
    opcao = st.radio("Selecione a ferramenta:", ["👤 Treinamentos", "🪜 Escadas"])
    
    st.divider()
    st.write("### 🛠️ Ações Rápidas")
    
    # Botão de Inspeção
    st.link_button("📝 Nova Inspeção (Forms)", "https://docs.google.com/forms/d/e/1FAIpQLScyv4M1N9A9v8p6O-n9x_r4_0o-p5W-v7Y-f9-0o-p5W-v7Y-f9-0o-p5W-v7Y-f9-0o-p5W-v7Y/viewform")
    
    if st.button("🔄 Atualizar Dados"):
        st.rerun()

# --- ROTEADOR DE TELAS ---
if opcao == "👤 Treinamentos":
    tela_treinamentos()
else:
    tela_escadas()

# --- RODAPÉ PERSONALIZADO COM COPYRIGHT ---
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: #7d7d7d;
        text-align: center;
        padding: 10px;
        font-size: 13px;
        border-top: 1px solid #eaeaea;
        z-index: 999;
    }
    </style>
    <div class="footer">
        © 2026 [Dilceu Junior]. Todos os direitos reservados. <br>
        <span style="font-size: 11px;">Desenvolvido por JuniorAmaral</span>
    </div>
    """,
    unsafe_allow_html=True
)


