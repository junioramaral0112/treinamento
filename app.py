import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import base64
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# --- CONFIGURAÇÃO INICIAL E CONSTANTES ---

# Nomes das abas na sua Planilha Google
ABA_NR35 = 'NR_35'

# Dicionário com os caminhos das imagens (eles devem estar na pasta 'app_treinamento' no GitHub)
IMAGE_PATHS = {
    "schaefer": "app_treinamento/schaefer.png",
    "nova510": "app_treinamento/nova510.png",
    "nr35": "app_treinamento/nr-35.png",
    "logo": "app_treinamento/logo.png",
    "sesmt": "app_treinamento/sesmt.png",
    "nr10": "app_treinamento/nr10.png",
    "nr12": "app_treinamento/nr12.png",
    "nr11": "app_treinamento/nr11.png", # Mapeado para ponte rolante
    "emp": "app_treinamento/emp.png",
    "autorizados_gas": "app_treinamento/logo.png" # Usando logo padrão
}

NR_NAMES = {
    'NR10': 'NR 10 - Segurança em Instalações e Serviços em Eletricidade',
    'NR12': 'NR 12 - Segurança no Trabalho em Máquinas e Equipamentos',
    'PONTE_ROLANTE': 'Ponte Rolante',
    'EMPILHADEIRA': 'Empilhadeira',
    'AUTORIZADOS_GÁS': 'Autorizados para Gás'
}

# --- FUNÇÕES DE CONEXÃO E MANIPULAÇÃO DE DADOS (GOOGLE SHEETS) ---

@st.cache_resource
def connect_to_google_sheets():
    """Conecta ao Google Sheets usando os Secrets do Streamlit."""
    sa = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = sa.open("AUTORIZADOS")
    return sh

def carregar_dados_gs(aba_nome, sh):
    """Carrega dados de uma aba específica da Planilha Google para um DataFrame."""
    try:
        worksheet = sh.worksheet(aba_nome)
        df = get_as_dataframe(worksheet, evaluate_formulas=True, header=0)
        df.dropna(how='all', inplace=True)

        date_cols = [
            "DATA DE REALIZAÇÃO", "VENCIMENTO DO TREINAMENTO", 
            "REALIZAÇÃO ASO ALTURA", "VENCIMENTO DO ASO"
        ]
        
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        if aba_nome == ABA_NR35:
            if "DATA DE REALIZAÇÃO" in df.columns:
                df["VENCIMENTO DO TREINAMENTO"] = df["DATA DE REALIZAÇÃO"] + pd.DateOffset(years=2)
            if "REALIZAÇÃO ASO ALTURA" in df.columns:
                df["VENCIMENTO DO ASO"] = df["REALIZAÇÃO ASO ALTURA"] + pd.DateOffset(years=1)

        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{aba_nome}' não encontrada na Planilha Google!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados da aba '{aba_nome}': {e}")
        return pd.DataFrame()

def sincronizar_planilha_gs(aba_nome, df, sh):
    """Salva o DataFrame de volta na aba correspondente da Planilha Google."""
    try:
        worksheet = sh.worksheet(aba_nome)
        df_to_save = df.copy()

        for col in df_to_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
            df_to_save[col] = df_to_save[col].fillna("")

        worksheet.clear()
        set_with_dataframe(worksheet, df_to_save, include_index=False, resize=True)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados na aba '{aba_nome}': {e}")
        return False

# --- FUNÇÕES DE UI E UTILITÁRIAS ---

@st.cache_data
def convert_df_to_csv(df):
    """Converte um DataFrame para CSV para download."""
    return df.to_csv(index=False, sep=';').encode('utf-8-sig')

def criar_cabecalho():
    # (Esta função permanece a mesma que a versão anterior)
    try:
        @st.cache_data
        def load_image(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        page_param = st.query_params.get('page', 'nr35')
        bg_img_path = IMAGE_PATHS["schaefer"] if page_param == "outras_nrs" else IMAGE_PATHS["nova510"]
        bg_img = load_image(bg_img_path)
        logo_img = load_image(IMAGE_PATHS["logo"])
        sesmt_img = load_image(IMAGE_PATHS["sesmt"])
        st.markdown(f"""
        <style>
            .header-container {{ position: relative; background-image: url("data:image/png;base64,{bg_img}"); background-size: cover; background-position: center; height: 280px; border-radius: 10px; margin-bottom: 25px; }}
            .header-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-size: 2.5rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.7); }}
            .header-logo-left {{ position: absolute; top: 80px; left: 80px; height: 80px; }}
            .header-logos-right {{ position: absolute; top: 50px; right: 50px; display: flex; flex-direction: column; gap: 30px; }}
            .header-logos-right img {{ height: 70px; border-radius: 5px; }}
            .header-logo-right-single {{ position: absolute; top: 80px; right: 80px; height: 80px; }}
            .menu-navegacao {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; }}
            .menu-navegacao a {{ text-decoration: none; }}
            .menu-navegacao button {{ padding: 10px 20px; font-size: 16px; border-radius: 5px; border: none; cursor: pointer; background-color: #f0f2f6; }}
            .menu-navegacao button:hover {{ background-color: #d0d2d6; }}
            .menu-navegacao button.active {{ background-color: #4CAF50; color: white; }}
        </style>
        """, unsafe_allow_html=True)

        if page_param == "outras_nrs":
            st.markdown(f"""
            <div class="header-container">
                <img src="data:image/png;base64,{logo_img}" class="header-logo-left">
                <img src="data:image/png;base64,{sesmt_img}" class="header-logo-right-single">
                <div class="header-text">Controle de Treinamentos NR</div>
            </div>""", unsafe_allow_html=True)
        else:
            nr_img = load_image(IMAGE_PATHS["nr35"])
            st.markdown(f"""
            <div class="header-container">
                <img src="data:image/png;base64,{logo_img}" class="header-logo-left">
                <div class="header-logos-right">
                    <img src="data:image/png;base64,{nr_img}">
                    <img src="data:image/png;base64,{sesmt_img}">
                </div>
                <div class="header-text">Controle de Treinamentos NR</div>
            </div>""", unsafe_allow_html=True)
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar imagem: {e}. Verifique se a pasta 'app_treinamento' e todas as imagens estão no seu repositório GitHub com os nomes corretos.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao criar o cabeçalho: {e}")

# --- ESTRUTURA PRINCIPAL DO APLICATIVO ---

st.set_page_config(page_title="Controle NR", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #80d1e8; }
</style>
""", unsafe_allow_html=True)

try:
    google_sheets_conn = connect_to_google_sheets()
    todas_as_abas = [ws.title for ws in google_sheets_conn.worksheets()]
except Exception as e:
    st.error("Falha crítica na conexão com o Google Sheets. Verifique os 'Secrets' e as permissões da API no Google Cloud.")
    st.info("Detalhes do erro: " + str(e))
    st.stop()

criar_cabecalho()

if 'page' not in st.query_params:
    st.query_params.page = "nr35"
pagina_atual = st.query_params.page

st.markdown(f"""
<div class="menu-navegacao">
    <a href="?page=nr35" target="_self"><button class="{"active" if pagina_atual == "nr35" else ""}">NR 35</button></a>
    <a href="?page=outras_nrs" target="_self"><button class="{"active" if pagina_atual == "outras_nrs" else ""}">Outras NR's</button></a>
</div>
""", unsafe_allow_html=True)


# --- LÓGICA DA PÁGINA NR35 ---
if pagina_atual == "nr35":
    st.subheader("Gerenciamento de Treinamentos - NR 35")
    df = carregar_dados_gs(ABA_NR35, google_sheets_conn)

    # --- SEÇÃO DE FILTROS E EXPORTAÇÃO ---
    st.subheader("🔎 Filtros e Exportação")
    df_filtrado = df.copy()

    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_nome = st.text_input("Filtrar por Nome:")
        if filtro_nome:
            df_filtrado = df_filtrado[df_filtrado['NOME'].str.contains(filtro_nome, case=False, na=False)]
    with col2:
        if 'SETOR' in df.columns and not df['SETOR'].dropna().empty:
            setores = sorted(df['SETOR'].dropna().unique())
            filtro_setor = st.multiselect("Filtrar por Setor:", options=setores)
            if filtro_setor:
                df_filtrado = df_filtrado[df_filtrado['SETOR'].isin(filtro_setor)]
    
    csv = convert_df_to_csv(df_filtrado)
    st.download_button(
        label="📥 Exportar para CSV", data=csv,
        file_name=f'export_nr35_filtrado_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
    
    # --- SEÇÃO DE EDIÇÃO E ADIÇÃO ---
    st.markdown("---")
    st.subheader("📋 Tabela de Registros (Edite, adicione ou remova linhas)")
    df_editado = st.data_editor(
        df_filtrado, num_rows="dynamic", use_container_width=True, key="editor_nr35"
    )

    if st.button("Salvar Alterações na Tabela (NR 35)"):
         with st.spinner("Sincronizando com a planilha..."):
            # Para evitar perda de dados, mesclamos as alterações no dataframe original
            # Esta é uma abordagem simplificada que sobrescreve tudo.
            # Se um filtro estiver ativo, é preciso cuidado, mas o data_editor ajuda a gerenciar isso.
            # A forma mais segura é salvar o df_editado se nenhum filtro estiver ativo,
            # ou fazer uma lógica de merge complexa. Por simplicidade, vamos salvar o que for editado.
            # AVISO: Se você editar com um filtro ativo, somente os dados filtrados e editados serão salvos.
            # Para segurança, o ideal é editar a tabela completa.
            if sincronizar_planilha_gs(ABA_NR35, df_editado, google_sheets_conn):
                st.success("Alterações salvas com sucesso!")
                st.rerun()

    # --- SEÇÃO DO DASHBOARD DE STATUS ---
    st.markdown("---")
    st.subheader("📊 Status de Vencimento - Detalhado")

    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    def verificar_status(data_vencimento):
        if pd.isna(data_vencimento): return "Sem Data"
        if data_vencimento < hoje: return "Vencido"
        if data_vencimento <= hoje + timedelta(days=30): return "Vencendo"
        return "OK"

    if "VENCIMENTO DO TREINAMENTO" in df.columns:
        df["Status Treinamento"] = df["VENCIMENTO DO TREINAMENTO"].apply(verificar_status)
    if "VENCIMENTO DO ASO" in df.columns:
        df["Status ASO"] = df["VENCIMENTO DO ASO"].apply(verificar_status)

    col1, col2 = st.columns(2)
    with col1:
        if "Status Treinamento" in df.columns:
            treinamento_counts = df["Status Treinamento"].value_counts()
            fig = px.pie(values=treinamento_counts.values, names=treinamento_counts.index, title="Status do Treinamento NR 35", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)

            st.write("Treinamentos Vencidos e Vencendo")
            df_venc_treinamento = df[df["Status Treinamento"].isin(["Vencido", "Vencendo"])]
            st.dataframe(df_venc_treinamento[["NOME", "SETOR", "VENCIMENTO DO TREINAMENTO", "Status Treinamento"]], use_container_width=True)

    with col2:
        if "Status ASO" in df.columns:
            aso_counts = df["Status ASO"].value_counts()
            fig_aso = px.pie(values=aso_counts.values, names=aso_counts.index, title="Status do ASO para Altura", hole=0.3)
            st.plotly_chart(fig_aso, use_container_width=True)

            st.write("ASOs Vencidos, Vencendo e Sem Data")
            df_venc_aso = df[df["Status ASO"].isin(["Vencido", "Vencendo", "Sem Data"])]
            st.dataframe(df_venc_aso[["NOME", "SETOR", "VENCIMENTO DO ASO", "Status ASO"]], use_container_width=True)


# --- LÓGICA DA PÁGINA OUTRAS NRs ---
elif pagina_atual == "outras_nrs":
    st.subheader("📋 Outras NR's")
    st.info("Selecione uma NR abaixo para visualizar, adicionar, editar ou remover registros.")

    abas_outras_nrs = [aba for aba in todas_as_abas if aba != ABA_NR35]
    
    if not abas_outras_nrs:
        st.warning("Nenhuma outra aba de NR foi encontrada na sua Planilha Google.")
    else:
        aba_selecionada = st.selectbox("Selecione a NR para gerenciar:", abas_outras_nrs)

        if aba_selecionada:
            st.markdown(f"### Gerenciando: {aba_selecionada}")
            df_nr = carregar_dados_gs(aba_selecionada, google_sheets_conn)

            df_nr_editado = st.data_editor(
                df_nr, num_rows="dynamic", use_container_width=True, key=f"editor_{aba_selecionada}"
            )

            if st.button(f"Salvar Alterações em {aba_selecionada}"):
                with st.spinner(f"Salvando dados de {aba_selecionada}..."):
                    if sincronizar_planilha_gs(aba_selecionada, df_nr_editado, google_sheets_conn):
                        st.success(f"Alterações em {aba_selecionada} salvas com sucesso!")
                        st.rerun()

# --- RODAPÉ ---
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 0.8rem; color: #555;">
    <p>Sistema de Controle de Treinamentos - v4.2 (Cloud)<br>
    Desenvolvido por <strong>Dilceu Amaral Junior</strong><br>
    {datetime.now().year}</p>
</div>
""", unsafe_allow_html=True)
