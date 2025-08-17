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

# Usa o cache do Streamlit para evitar reconectar a cada interação
@st.cache_resource
def connect_to_google_sheets():
    """Conecta ao Google Sheets usando os Secrets do Streamlit."""
    sa = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    # NOME CORRIGIDO DA SUA PLANILHA
    sh = sa.open("AUTORIZADOS")
    return sh

def carregar_dados_gs(aba_nome, sh):
    """Carrega dados de uma aba específica da Planilha Google para um DataFrame."""
    try:
        worksheet = sh.worksheet(aba_nome)
        # Carrega os dados, permitindo que o pandas tente inferir os tipos
        df = get_as_dataframe(worksheet, evaluate_formulas=True, header=0)
        df.dropna(how='all', inplace=True)

        # Define as colunas que devem ser tratadas como datas
        date_cols = [
            "DATA DE REALIZAÇÃO", "VENCIMENTO DO TREINAMENTO",
            "REALIZAÇÃO ASO ALTURA", "VENCIMENTO DO ASO"
        ]
        
        # Converte as colunas de data, transformando qualquer erro em NaT (Not a Time)
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Recalcula vencimentos (específico da NR35) de forma segura
        if aba_nome == ABA_NR35:
            if "DATA DE REALIZAÇÃO" in df.columns:
                # A operação de soma agora é segura, pois a coluna é garantidamente do tipo datetime
                # A soma de NaT com DateOffset resulta em NaT, o que evita erros.
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

        # Converte colunas de data para string no formato AAAA-MM-DD para evitar problemas de fuso horário
        for col in df_to_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                df_to_save[col] = df_to_save[col].dt.strftime('%Y-%m-%d')
            # Garante que valores nulos sejam salvos como strings vazias
            df_to_save[col] = df_to_save[col].fillna("")


        # Limpa a aba e escreve o novo conteúdo
        worksheet.clear()
        set_with_dataframe(worksheet, df_to_save, include_index=False, resize=True)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados na aba '{aba_nome}': {e}")
        return False

# --- FUNÇÕES DE INTERFACE GRÁFICA ---

def criar_cabecalho():
    """Cria o cabeçalho visual da página."""
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

    # Sessão para Adicionar novo registro
    with st.expander("➕ Adicionar Novo Registro na NR35"):
        with st.form("novo_registro_form_nr35", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                nome = st.text_input("NOME*", key="nr35_nome")
                opcoes_unidade = sorted(['Biguaçu', 'Floripa', 'Palhoça'])
                unidade = st.selectbox("UNIDADE*", options=opcoes_unidade, index=None, placeholder="Selecione...", key="nr35_unidade")
                opcoes_setor = sorted(['Acabamento', 'Astec', 'Desmolde', 'Elétrica', 'Estofaria', 'Gel', 'Laminação', 'Modelagem', 'Pintura', 'Rebarba'])
                setor = st.selectbox("SETOR*", options=opcoes_setor, index=None, placeholder="Selecione...", key="nr35_setor")
            with cols[1]:
                data_realizacao = st.date_input("Data de Realização do TREINAMENTO*", value=None, key="nr35_data_treinamento")
                data_aso_realizacao = st.date_input("Data de Realização do ASO", value=None, key="nr35_data_aso")
                aso_altura = st.selectbox("ASO ALTURA*", ["Apto", "Inapto"], key="nr35_aso_altura")

            observacao = st.text_input("OBSERVAÇÃO", key="nr35_obs")
            
            if st.form_submit_button("Adicionar Registro"):
                if not all([nome, unidade, setor, data_realizacao]):
                    st.warning("Preencha todos os campos obrigatórios (*)")
                else:
                    novo_registro = pd.DataFrame([{
                        "NOME": nome, "UNIDADE": unidade, "SETOR": setor,
                        "DATA DE REALIZAÇÃO": pd.to_datetime(data_realizacao),
                        "REALIZAÇÃO ASO ALTURA": pd.to_datetime(data_aso_realizacao) if data_aso_realizacao else pd.NaT,
                        "ASO ALTURA": aso_altura,
                        "OBSERVAÇÃO": observacao
                    }])
                    df_atualizado = pd.concat([df, novo_registro], ignore_index=True)
                    
                    with st.spinner("Adicionando e salvando..."):
                        if sincronizar_planilha_gs(ABA_NR35, df_atualizado, google_sheets_conn):
                            st.success("Registro adicionado com sucesso!")
                            st.rerun()

    st.markdown("---")
    st.subheader("📋 Tabela de Registros (NR 35)")
    st.info("Clique nas células para editar. Adicione ou remova linhas e depois clique no botão 'Salvar Alterações na Tabela' abaixo.")
    
    df_editado = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key="editor_nr35"
    )

    if st.button("Salvar Alterações na Tabela (NR 35)"):
         with st.spinner("Sincronizando com a planilha..."):
            if sincronizar_planilha_gs(ABA_NR35, df_editado, google_sheets_conn):
                st.success("Alterações salvas com sucesso!")
                st.rerun()

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
    <p>Sistema de Controle de Treinamentos - v4.1 (Cloud)<br>
    Desenvolvido por <strong>Dilceu Amaral Junior</strong><br>
    {datetime.now().year}</p>
</div>
""", unsafe_allow_html=True)
