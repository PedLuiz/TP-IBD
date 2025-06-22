import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime
import warnings

# Configurações
warnings.filterwarnings('ignore')
st.set_page_config(
    page_title="Dashboard de Importações Brasil 2024",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    
    .stSelectbox > div > div {
        background-color: #ffffff;
    }
    
    .plot-container {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares para SQLite
@st.cache_resource
def get_connection():
    """Conecta ao banco SQLite"""
    try:
        conn = sqlite3.connect('importacoes_brasil_2024.db')
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

@st.cache_data
def fetch_data(query, _conn):
    """Executa query e retorna DataFrame"""
    try:
        return pd.read_sql_query(query, _conn)
    except Exception as e:
        st.error(f"Erro ao executar query: {e}")
        return pd.DataFrame()

@st.cache_data
def get_basic_stats(_conn):
    """Retorna estatísticas básicas do banco"""
    try:
        stats = {}
        
        # Total de importações
        total_query = "SELECT COUNT(*) as total FROM Importacoes"
        stats['total_imports'] = fetch_data(total_query, _conn)['total'].iloc[0]
        
        # Valor total FOB
        value_query = "SELECT SUM(VL_FOB) as total_value FROM Importacoes"
        stats['total_value'] = fetch_data(value_query, _conn)['total_value'].iloc[0]
        
        # Países únicos
        countries_query = "SELECT COUNT(DISTINCT COD_PAIS) as countries FROM Importacoes"
        stats['unique_countries'] = fetch_data(countries_query, _conn)['countries'].iloc[0]
        
        # NCMs únicos
        ncm_query = "SELECT COUNT(DISTINCT COD_NCM) as ncms FROM Importacoes"
        stats['unique_ncms'] = fetch_data(ncm_query, _conn)['ncms'].iloc[0]
        
        return stats
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return {}

def format_number(number):
    """Formata números para exibição"""
    if number >= 1e9:
        return f"{number/1e9:.2f}B"
    elif number >= 1e6:
        return f"{number/1e6:.2f}M"
    elif number >= 1e3:
        return f"{number/1e3:.2f}K"
    else:
        return f"{number:.2f}"

def build_sql_filters(periodo_selecionado, regiao_selecionada, valor_minimo, periodo_opcoes, regioes_opcoes):
    """Constrói filtros SQL baseados nas seleções do usuário"""
    filters = []
    
    # Filtro de período
    periodo_key = periodo_opcoes[periodo_selecionado]
    if periodo_key == "primeiro_semestre":
        filters.append("i.COD_MES <= 6")
    elif periodo_key == "segundo_semestre":
        filters.append("i.COD_MES > 6")
    elif periodo_key == "primeiro_trimestre":
        filters.append("i.COD_MES <= 3")
    elif periodo_key == "segundo_trimestre":
        filters.append("i.COD_MES BETWEEN 4 AND 6")
    elif periodo_key == "terceiro_trimestre":
        filters.append("i.COD_MES BETWEEN 7 AND 9")
    elif periodo_key == "quarto_trimestre":
        filters.append("i.COD_MES >= 10")
    
    # Filtro de região
    if regiao_selecionada != "🇧🇷 Brasil Completo":
        ufs_regiao = regioes_opcoes[regiao_selecionada]
        ufs_str = "', '".join(ufs_regiao)
        filters.append(f"uf.SIGLA_UF IN ('{ufs_str}')")
    
    # Filtro de valor mínimo
    if valor_minimo == "Acima de US$ 1.000":
        filters.append("i.VL_FOB >= 1000")
    elif valor_minimo == "Acima de US$ 10.000":
        filters.append("i.VL_FOB >= 10000")
    elif valor_minimo == "Acima de US$ 100.000":
        filters.append("i.VL_FOB >= 100000")
    elif valor_minimo == "Acima de US$ 1.000.000":
        filters.append("i.VL_FOB >= 1000000")
    
    # Retornar string WHERE ou vazia
    if filters:
        return "WHERE " + " AND ".join(filters)
    return ""

def main():
    # Header principal
    st.markdown('<h1 class="main-header">Dashboard de Importações Brasil 2024</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: rgb(102, 102, 102);">
            Análise exploratória completa dos dados de importações brasileiras por código NCM
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Conectar ao banco
    conn = get_connection()
    if conn is None:
        st.error("❌ Não foi possível conectar ao banco de dados. Verifique se o arquivo 'importacoes_brasil_2024.db' existe.")
        return
    
    # Sidebar para filtros
    st.sidebar.markdown('<div class="sidebar-header">🔍 Filtros de Análise</div>', 
                       unsafe_allow_html=True)
    
    # Obter opções para filtros
    try:
        # Meses
        meses = fetch_data("SELECT DISTINCT COD_MES, NOME_MES FROM Mes ORDER BY COD_MES", conn)
        mes_options = {f"{row['NOME_MES']} ({row['COD_MES']})": row['COD_MES'] 
                      for _, row in meses.iterrows()}
        
        # Países (top 20 por valor)
        top_paises = fetch_data("""
            SELECT p.COD_PAIS, p.NOME_PAIS, SUM(i.VL_FOB) as total_value
            FROM Importacoes i
            JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
            GROUP BY p.COD_PAIS, p.NOME_PAIS
            ORDER BY total_value DESC
            LIMIT 20
        """, conn)
        
        # UFs
        ufs = fetch_data("SELECT DISTINCT COD_UF, NOME_UF FROM UF ORDER BY NOME_UF", conn)
        uf_options = {f"{row['NOME_UF']}": row['COD_UF'] for _, row in ufs.iterrows()}
        
    except Exception as e:
        st.error(f"Erro ao carregar opções de filtro: {e}")
        return    # Filtros na sidebar - Simplificados e mais intuitivos
    
    st.sidebar.info(
        "💡 **Dica:** Use estes filtros para focar suas análises em períodos, regiões ou valores específicos. "
        "Os gráficos se atualizarão automaticamente!"
    )
    
    # Filtro de período mais simples
    periodo_opcoes = {
        "Ano Completo (2024)": "completo",
        "1º Semestre": "primeiro_semestre", 
        "2º Semestre": "segundo_semestre",
        "1º Trimestre": "primeiro_trimestre",
        "2º Trimestre": "segundo_trimestre", 
        "3º Trimestre": "terceiro_trimestre",
        "4º Trimestre": "quarto_trimestre"
    }
    
    periodo_selecionado = st.sidebar.selectbox(
        "📅 Período de Análise",
        options=list(periodo_opcoes.keys()),
        index=0
    )
    
    # Filtro de top países mais simples
    st.sidebar.markdown("### 🌍 Foco Geográfico")
    num_paises = st.sidebar.slider(
        "Número de Países (Top por Valor)",
        min_value=5,
        max_value=25,
        value=10,
        step=5,
        help="Selecione quantos países principais incluir nas análises"
    )
    
    # Filtro de análise regional
    regioes_opcoes = {
        "Brasil Completo": "todas",
        "Sudeste": ["SP", "RJ", "MG", "ES"],
        "Sul": ["RS", "SC", "PR"], 
        "Nordeste": ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "SE", "PI"],
        "Norte": ["AM", "PA", "RO", "AC", "RR", "AP", "TO"],
        "Centro-Oeste": ["GO", "MT", "MS", "DF"]
    }
    
    regiao_selecionada = st.sidebar.selectbox(
        "🗺️ Região do Brasil",
        options=list(regioes_opcoes.keys()),
        index=0
    )
    
    # Filtro de valor mínimo
    st.sidebar.markdown("### 💰 Filtro de Valor")
    valor_minimo = st.sidebar.selectbox(
        "Valor Mínimo da Operação (US$)",
        options=["Todos os valores", "Acima de US$ 1.000", "Acima de US$ 10.000", "Acima de US$ 100.000", "Acima de US$ 1.000.000"],
        index=0,
        help="Filtrar operações por valor mínimo para focar em grandes importações"
    )
      # Estatísticas gerais
    st.markdown("## 📈 Visão Geral")
    
    # Mostrar filtros aplicados
    if (periodo_selecionado != "Ano Completo (2024)" or 
        regiao_selecionada != "Brasil Completo" or 
        valor_minimo != "Todos os valores"):
        
        filtros_ativos = []
        if periodo_selecionado != "Ano Completo (2024)":
            filtros_ativos.append(f"{periodo_selecionado}")
        if regiao_selecionada != "🇧Brasil Completo":
            filtros_ativos.append(f"{regiao_selecionada}")
        if valor_minimo != "Todos os valores":
            filtros_ativos.append(f"{valor_minimo}")
        
        st.info(f"🔍 **Filtros Aplicados:** {' • '.join(filtros_ativos)}")
    
    stats = get_basic_stats(conn)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>🚢 Total de Importações</h3>
                    <h2>{format_number(stats['total_imports'])}</h2>
                </div>
                """, unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>💰 Valor Total (FOB)</h3>
                    <h2>US$ {format_number(stats['total_value'])}</h2>
                </div>
                """, unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>🌍 Países Únicos</h3>
                    <h2>{stats['unique_countries']}</h2>
                </div>
                """, unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>📦 NCMs Únicos</h3>
                    <h2>{stats['unique_ncms']}</h2>
                </div>
                """, unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Análise Temporal", 
        "🌍 Análise por Países", 
        "🏛️ Análise por Estados",
        "📦 Análise por NCM",
        "🔍 Análise Detalhada"
    ])
    
    with tab1:
        st.markdown("### 📅 Evolução das Importações ao Longo do Ano")
        
        # Query para dados temporais
        temporal_query = """
        SELECT 
            m.NOME_MES,
            m.COD_MES,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN Mes m ON i.COD_MES = m.COD_MES
        GROUP BY m.COD_MES, m.NOME_MES
        ORDER BY m.COD_MES
        """
        
        df_temporal = fetch_data(temporal_query, conn)
        
        if not df_temporal.empty:
            # Gráfico de linha - Evolução temporal
            fig_temporal = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Valor Total das Importações (US$ FOB)',
                    'Número de Operações',
                    'Peso Total (kg)',
                    'Valor Médio por Operação (US$)'
                ),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Valor total
            fig_temporal.add_trace(
                go.Scatter(
                    x=df_temporal['NOME_MES'], 
                    y=df_temporal['valor_total'],
                    mode='lines+markers',
                    name='Valor Total',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=1
            )
            
            # Número de operações
            fig_temporal.add_trace(
                go.Scatter(
                    x=df_temporal['NOME_MES'], 
                    y=df_temporal['total_operacoes'],
                    mode='lines+markers',
                    name='Operações',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=2
            )
            
            # Peso total
            fig_temporal.add_trace(
                go.Scatter(
                    x=df_temporal['NOME_MES'], 
                    y=df_temporal['peso_total'],
                    mode='lines+markers',
                    name='Peso Total',
                    line=dict(color='#2ca02c', width=3),
                    marker=dict(size=8)
                ),
                row=2, col=1
            )
            
            # Valor médio
            fig_temporal.add_trace(
                go.Scatter(
                    x=df_temporal['NOME_MES'], 
                    y=df_temporal['valor_medio'],
                    mode='lines+markers',
                    name='Valor Médio',
                    line=dict(color='#d62728', width=3),
                    marker=dict(size=8)
                ),
                row=2, col=2
            )
            
            fig_temporal.update_layout(
                height=600,
                showlegend=False,
                title_text="📈 Análise Temporal das Importações - 2024"
            )
            
            # Rotacionar labels do eixo x
            fig_temporal.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig_temporal, use_container_width=True)
            
            # Análise de sazonalidade
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras - Valor por trimestre
                df_temporal['trimestre'] = ((df_temporal['COD_MES'] - 1) // 3) + 1
                trimestre_data = df_temporal.groupby('trimestre').agg({
                    'valor_total': 'sum',
                    'total_operacoes': 'sum'
                }).reset_index()
                
                fig_trimestre = px.bar(
                    trimestre_data,
                    x='trimestre',
                    y='valor_total',
                    title='💰 Valor Total por Trimestre',
                    labels={'trimestre': 'Trimestre', 'valor_total': 'Valor Total (US$)'},
                    color='valor_total',
                    color_continuous_scale='Blues'
                )
                fig_trimestre.update_layout(height=400)
                st.plotly_chart(fig_trimestre, use_container_width=True)
            
            with col2:
                # Gráfico de pizza - Distribuição por semestre
                df_temporal['semestre'] = ((df_temporal['COD_MES'] - 1) // 6) + 1
                semestre_data = df_temporal.groupby('semestre')['valor_total'].sum().reset_index()
                semestre_data['semestre_label'] = semestre_data['semestre'].apply(
                    lambda x: f"{x}º Semestre"
                )
                
                fig_semestre = px.pie(
                    semestre_data,
                    values='valor_total',
                    names='semestre_label',
                    title='📊 Distribuição por Semestre',
                    color_discrete_sequence=['#1f77b4', '#ff7f0e']
                )
                fig_semestre.update_layout(height=400)
                st.plotly_chart(fig_semestre, use_container_width=True)
    
    with tab2:
        st.markdown("### 🌍 Análise por Países de Origem")
        
        # Query para dados por país
        paises_query = """
        SELECT 
            p.NOME_PAIS,
            p.COD_PAIS,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio,
            SUM(i.VL_FRETE) as frete_total,
            SUM(i.VL_SEGURO) as seguro_total
        FROM Importacoes i
        JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        GROUP BY p.COD_PAIS, p.NOME_PAIS
        ORDER BY valor_total DESC
        LIMIT 20
        """
        
        df_paises = fetch_data(paises_query, conn)
        
        if not df_paises.empty:
            # Top 15 países por valor
            col1, col2 = st.columns(2)
            
            with col1:
                fig_paises_bar = px.bar(
                    df_paises.head(15),
                    x='valor_total',
                    y='NOME_PAIS',
                    title='💰 Top 15 Países por Valor Total (US$ FOB)',
                    labels={'valor_total': 'Valor Total (US$)', 'NOME_PAIS': 'País'},
                    color='valor_total',
                    color_continuous_scale='Viridis',
                    orientation='h'
                )
                fig_paises_bar.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_paises_bar, use_container_width=True)
            
            with col2:
                # Gráfico de dispersão - Valor vs Operações
                fig_scatter = px.scatter(
                    df_paises.head(15),
                    x='total_operacoes',
                    y='valor_total',
                    size='peso_total',
                    color='valor_medio',
                    hover_name='NOME_PAIS',
                    title='🔍 Valor vs Número de Operações',
                    labels={
                        'total_operacoes': 'Número de Operações',
                        'valor_total': 'Valor Total (US$)',
                        'valor_medio': 'Valor Médio (US$)'
                    },
                    color_continuous_scale='plasma'
                )
                fig_scatter.update_layout(height=600)
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Mapa de calor - Top países por mês
            paises_mes_query = """
            SELECT 
                p.NOME_PAIS,
                m.NOME_MES,
                SUM(i.VL_FOB) as valor_total
            FROM Importacoes i
            JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
            JOIN Mes m ON i.COD_MES = m.COD_MES
            WHERE p.NOME_PAIS IN ({})
            GROUP BY p.NOME_PAIS, m.NOME_MES, m.COD_MES
            ORDER BY m.COD_MES
            """.format(','.join([f"'{pais}'" for pais in df_paises.head(10)['NOME_PAIS']]))
            
            df_heatmap = fetch_data(paises_mes_query, conn)
            
            if not df_heatmap.empty:
                # Pivot para heatmap
                heatmap_data = df_heatmap.pivot(
                    index='NOME_PAIS', 
                    columns='NOME_MES', 
                    values='valor_total'
                ).fillna(0)
                
                fig_heatmap = px.imshow(
                    heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    title='🌡️ Heatmap: Valor das Importações por País e Mês',
                    labels=dict(x="Mês", y="País", color="Valor (US$)"),
                    color_continuous_scale='RdYlBu_r'
                )
                fig_heatmap.update_layout(height=500)
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab3:
        st.markdown("### 🏛️ Análise por Estados Brasileiros")
        
        # Query para dados por UF
        uf_query = """
        SELECT 
            uf.NOME_UF,
            uf.SIGLA_UF,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN UF uf ON i.COD_UF = uf.COD_UF
        GROUP BY uf.COD_UF, uf.NOME_UF, uf.SIGLA_UF
        ORDER BY valor_total DESC
        """
        
        df_ufs = fetch_data(uf_query, conn)
        
        if not df_ufs.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 15 UFs por valor
                fig_ufs = px.bar(
                    df_ufs.head(15),
                    x='SIGLA_UF',
                    y='valor_total',
                    title='🏛️ Top 15 Estados por Valor Total',
                    labels={'valor_total': 'Valor Total (US$)', 'SIGLA_UF': 'Estado'},
                    color='valor_total',
                    color_continuous_scale='Blues',
                    hover_data=['NOME_UF', 'total_operacoes']
                )
                fig_ufs.update_layout(height=500)
                st.plotly_chart(fig_ufs, use_container_width=True)
            
            with col2:
                # Gráfico de pizza - Top 10 UFs
                top_ufs = df_ufs.head(10).copy()
                outros_valor = df_ufs.iloc[10:]['valor_total'].sum()
                
                if outros_valor > 0:
                    top_ufs = pd.concat([
                        top_ufs,
                        pd.DataFrame({
                            'SIGLA_UF': ['OUTROS'],
                            'valor_total': [outros_valor],
                            'NOME_UF': ['Outros Estados']
                        })
                    ])
                
                fig_pie_uf = px.pie(
                    top_ufs,
                    values='valor_total',
                    names='SIGLA_UF',
                    title='📊 Distribuição por Estado (Top 10 + Outros)',
                    hover_data=['NOME_UF']
                )
                fig_pie_uf.update_layout(height=500)
                st.plotly_chart(fig_pie_uf, use_container_width=True)
            
            # Análise de concentração por região
            st.markdown("#### 📍 Análise Regional")
            
            # Mapeamento manual de regiões (simplificado)
            regioes = {
                'SP': 'Sudeste', 'RJ': 'Sudeste', 'MG': 'Sudeste', 'ES': 'Sudeste',
                'RS': 'Sul', 'SC': 'Sul', 'PR': 'Sul',
                'BA': 'Nordeste', 'PE': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste',
                'PB': 'Nordeste', 'RN': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'PI': 'Nordeste',
                'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'DF': 'Centro-Oeste',
                'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'AC': 'Norte', 'RR': 'Norte', 'AP': 'Norte', 'TO': 'Norte'
            }
            
            df_ufs['REGIAO'] = df_ufs['SIGLA_UF'].map(regioes)
            df_regioes = df_ufs.groupby('REGIAO').agg({
                'valor_total': 'sum',
                'total_operacoes': 'sum',
                'peso_total': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_regiao_bar = px.bar(
                    df_regioes,
                    x='REGIAO',
                    y='valor_total',
                    title='🗺️ Valor Total por Região',
                    labels={'valor_total': 'Valor Total (US$)', 'REGIAO': 'Região'},
                    color='valor_total',
                    color_continuous_scale='Reds'
                )
                fig_regiao_bar.update_layout(height=400)
                st.plotly_chart(fig_regiao_bar, use_container_width=True)
            
            with col2:
                fig_regiao_pie = px.pie(
                    df_regioes,
                    values='valor_total',
                    names='REGIAO',
                    title='📊 Participação das Regiões'
                )
                fig_regiao_pie.update_layout(height=400)
                st.plotly_chart(fig_regiao_pie, use_container_width=True)
    
    with tab4:
        st.markdown("### 📦 Análise por Código NCM")
        
        # Query para dados por NCM
        ncm_query = """
        SELECT 
            n.COD_NCM,
            n.NOME_NCM,
            u.NOME_UNID,
            u.SIGLA_UNID,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            SUM(i.QT_ESTATISTICA) as quantidade_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN NCM n ON i.COD_NCM = n.COD_NCM
        JOIN Unidade u ON i.COD_UNID = u.COD_UNID
        GROUP BY n.COD_NCM, n.NOME_NCM, u.NOME_UNID, u.SIGLA_UNID
        ORDER BY valor_total DESC
        LIMIT 20
        """
        
        df_ncm = fetch_data(ncm_query, conn)
        
        if not df_ncm.empty:
            # Top NCMs por valor
            st.markdown("#### 💰 Top 20 NCMs por Valor Total")
            
            # Truncar nomes muito longos para visualização
            df_ncm['NOME_NCM_SHORT'] = df_ncm['NOME_NCM'].apply(
                lambda x: x[:50] + '...' if len(str(x)) > 50 else x
            )
            
            fig_ncm = px.bar(
                df_ncm.head(15),
                x='valor_total',
                y='NOME_NCM_SHORT',
                title='Top 15 NCMs por Valor Total (US$ FOB)',
                labels={'valor_total': 'Valor Total (US$)', 'NOME_NCM_SHORT': 'Produto NCM'},
                color='valor_total',
                color_continuous_scale='Greens',
                orientation='h',
                hover_data=['COD_NCM', 'SIGLA_UNID', 'total_operacoes']
            )
            fig_ncm.update_layout(height=700, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_ncm, use_container_width=True)
            
            # Análise de densidade de valor
            col1, col2 = st.columns(2)
            
            with col1:
                # Scatter plot - Valor vs Quantidade
                fig_scatter_ncm = px.scatter(
                    df_ncm.head(15),
                    x='quantidade_total',
                    y='valor_total',
                    size='total_operacoes',
                    color='valor_medio',
                    hover_name='NOME_NCM_SHORT',
                    title='🔍 Valor vs Quantidade por NCM',
                    labels={
                        'quantidade_total': 'Quantidade Total',
                        'valor_total': 'Valor Total (US$)',
                        'valor_medio': 'Valor Médio (US$)'
                    },
                    color_continuous_scale='viridis'
                )
                fig_scatter_ncm.update_layout(height=500)
                st.plotly_chart(fig_scatter_ncm, use_container_width=True)
            
            with col2:
                # Histograma de valor médio
                fig_hist_valor = px.histogram(
                    df_ncm,
                    x='valor_medio',
                    nbins=20,
                    title='📊 Distribuição do Valor Médio por Operação',
                    labels={'valor_medio': 'Valor Médio (US$)', 'count': 'Frequência'},
                    color_discrete_sequence=['#2ca02c']
                )
                fig_hist_valor.update_layout(height=500)
                st.plotly_chart(fig_hist_valor, use_container_width=True)
            
            # Tabela detalhada dos top NCMs
            st.markdown("#### 📋 Detalhamento dos Top NCMs")
            
            df_display = df_ncm.head(10)[['COD_NCM', 'NOME_NCM', 'SIGLA_UNID', 
                                        'total_operacoes', 'valor_total', 'valor_medio']].copy()
            df_display['valor_total'] = df_display['valor_total'].apply(lambda x: f"US$ {x:,.2f}")
            df_display['valor_medio'] = df_display['valor_medio'].apply(lambda x: f"US$ {x:,.2f}")
            df_display.columns = ['Código NCM', 'Descrição do Produto', 'Unidade', 
                                'Operações', 'Valor Total', 'Valor Médio']
            
            st.dataframe(df_display, use_container_width=True, height=400)
    
    with tab5:
        st.markdown("### 🔍 Análise Detalhada e Correlações")
        
        # Análise de correlações entre variáveis numéricas
        correlacao_query = """
        SELECT 
            VL_FOB as valor_fob,
            KG_LIQUIDO as peso_liquido,
            VL_FRETE as valor_frete,
            VL_SEGURO as valor_seguro,
            QT_ESTATISTICA as quantidade
        FROM Importacoes
        WHERE VL_FOB > 0 AND KG_LIQUIDO > 0
        LIMIT 10000
        """
        
        df_corr = fetch_data(correlacao_query, conn)
        
        if not df_corr.empty:
            st.markdown("#### 📊 Matriz de Correlação")
            
            # Calcular correlações
            corr_matrix = df_corr.corr()
            
            # Heatmap de correlação
            fig_corr = px.imshow(
                corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                title='Matriz de Correlação entre Variáveis',
                color_continuous_scale='RdBu',
                zmin=-1, zmax=1,
                text_auto=True
            )
            fig_corr.update_layout(height=500)
            st.plotly_chart(fig_corr, use_container_width=True)
              # Análises específicas de correlação
            st.markdown("#### 💎 Análises de Correlação Detalhadas")
            
            # Preparar dados para análises
            df_analysis = df_corr.copy()
            
            # Calcular preço por kg e percentual de frete
            df_analysis['preco_por_kg'] = df_analysis['valor_fob'] / df_analysis['peso_liquido']
            df_analysis['percentual_frete'] = (df_analysis['valor_frete'] / df_analysis['valor_fob']) * 100
            
            # Filtrar outliers extremos para melhor visualização
            q99_valor = df_analysis['valor_fob'].quantile(0.99)
            q99_peso = df_analysis['peso_liquido'].quantile(0.99)
            q99_frete = df_analysis['valor_frete'].quantile(0.99)
            
            df_filtered = df_analysis[
                (df_analysis['valor_fob'] <= q99_valor) & 
                (df_analysis['peso_liquido'] <= q99_peso) &
                (df_analysis['valor_frete'] <= q99_frete) &
                (df_analysis['valor_frete'] > 0) &
                (df_analysis['percentual_frete'] <= 50)  # Filtrar fretes muito altos
            ].sample(n=min(2000, len(df_analysis)))
            
            # Análise 1: Valor FOB vs Peso Líquido
            st.markdown("##### 💰 Análise: Valor FOB vs Peso Líquido")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig_valor_peso = px.scatter(
                    df_filtered,
                    x='peso_liquido',
                    y='valor_fob',
                    color='preco_por_kg',
                    title='Valor FOB vs Peso Líquido (Escala Logarítmica)',
                    labels={
                        'peso_liquido': 'Peso Líquido (kg)', 
                        'valor_fob': 'Valor FOB (US$)',
                        'preco_por_kg': 'Preço/kg (US$)'
                    },
                    opacity=0.7,
                    color_continuous_scale='Viridis',
                    log_x=True,
                    log_y=True,
                    hover_data={'preco_por_kg': ':.2f'}
                )
                
                fig_valor_peso.update_layout(
                    height=500,
                    annotations=[
                        dict(
                            x=0.02, y=0.98,
                            xref="paper", yref="paper",
                            text="🔍 Cores mais escuras = maior valor por kg",
                            showarrow=False,
                            bgcolor="rgba(255,255,255,0.8)",
                            font=dict(size=11)
                        )
                    ]
                )
                st.plotly_chart(fig_valor_peso, use_container_width=True)
            
            with col2:
                # Insights automáticos
                correlacao_valor_peso = df_filtered['valor_fob'].corr(df_filtered['peso_liquido'])
                mediana_preco_kg = df_filtered['preco_por_kg'].median()
                
                st.markdown("**📊 Insights:**")
                st.info(f"""
                • **Correlação:** {correlacao_valor_peso:.3f}
                • **Preço mediano:** US$ {mediana_preco_kg:.2f}/kg
                • **Padrão:** {'Correlação positiva moderada' if correlacao_valor_peso > 0.3 else 'Correlação fraca'}
                """)
                
                if correlacao_valor_peso > 0.5:
                    st.success("✅ Produtos mais pesados tendem a ter maior valor")
                elif correlacao_valor_peso < 0.3:
                    st.warning("⚠️ Relação fraca - produtos de alto valor agregado")
            
            # Análise 2: Frete vs Valor FOB
            st.markdown("##### 🚢 Análise: Custo de Frete vs Valor FOB")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig_frete_valor = px.scatter(
                    df_filtered,
                    x='valor_fob',
                    y='valor_frete',
                    color='percentual_frete',
                    title='Valor do Frete vs Valor FOB (Escala Logarítmica)',
                    labels={
                        'valor_fob': 'Valor FOB (US$)', 
                        'valor_frete': 'Valor do Frete (US$)',
                        'percentual_frete': '% Frete'
                    },
                    opacity=0.7,
                    color_continuous_scale='Plasma',
                    log_x=True,
                    log_y=True,
                    hover_data={'percentual_frete': ':.1f'}
                )
                
                # Adicionar linha de referência (5% do valor FOB)
                x_range = [df_filtered['valor_fob'].min(), df_filtered['valor_fob'].max()]
                y_ref = [x * 0.05 for x in x_range]
                
                fig_frete_valor.add_trace(
                    go.Scatter(
                        x=x_range, y=y_ref,
                        mode='lines',
                        name='Referência 5%',
                        line=dict(color='red', dash='dash', width=2),
                        hovertemplate='Referência: 5% do valor FOB'
                    )
                )
                
                fig_frete_valor.update_layout(
                    height=500,
                    annotations=[
                        dict(
                            x=0.02, y=0.98,
                            xref="paper", yref="paper",
                            text="🔍 Cores mais claras = maior % de frete",
                            showarrow=False,
                            bgcolor="rgba(255,255,255,0.8)",
                            font=dict(size=11)
                        ),
                        dict(
                            x=0.02, y=0.90,
                            xref="paper", yref="paper",
                            text="📏 Linha vermelha = 5% de referência",
                            showarrow=False,
                            bgcolor="rgba(255,255,255,0.8)",
                            font=dict(size=11)
                        )
                    ]
                )
                st.plotly_chart(fig_frete_valor, use_container_width=True)
            
            with col2:
                # Insights automáticos para frete
                correlacao_frete_valor = df_filtered['valor_fob'].corr(df_filtered['valor_frete'])
                mediana_percentual_frete = df_filtered['percentual_frete'].median()
                frete_alto = (df_filtered['percentual_frete'] > 10).mean() * 100
                
                st.markdown("**📊 Insights:**")
                st.info(f"""
                • **Correlação:** {correlacao_frete_valor:.3f}
                • **% Frete mediano:** {mediana_percentual_frete:.1f}%
                • **Frete alto (>10%):** {frete_alto:.1f}% dos casos
                """)
                
                if mediana_percentual_frete > 8:
                    st.warning("⚠️ Frete relativamente alto")
                else:
                    st.success("✅ Frete dentro da média esperada")
            
            # Análise 3: Distribuição do Percentual de Frete
            st.markdown("##### 📊 Distribuição dos Custos de Frete")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma do percentual de frete
                fig_hist_frete = px.histogram(
                    df_filtered,
                    x='percentual_frete',
                    nbins=30,
                    title='Distribuição do Percentual de Frete',
                    labels={'percentual_frete': 'Percentual do Frete (%)', 'count': 'Frequência'},
                    color_discrete_sequence=['#2E8B57']
                )
                
                # Adicionar linha da mediana
                fig_hist_frete.add_vline(
                    x=mediana_percentual_frete, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text=f"Mediana: {mediana_percentual_frete:.1f}%"
                )
                
                fig_hist_frete.update_layout(height=400)
                st.plotly_chart(fig_hist_frete, use_container_width=True)
            
            with col2:
                # Box plot do percentual de frete
                fig_box_frete = px.box(
                    df_filtered,
                    y='percentual_frete',
                    title='Box Plot: Percentual de Frete',
                    labels={'percentual_frete': 'Percentual do Frete (%)'}
                )
                
                fig_box_frete.update_layout(height=400)
                st.plotly_chart(fig_box_frete, use_container_width=True)
            
            # Resumo das correlações
            st.markdown("##### 📈 Resumo das Correlações")
            
            correlacoes_resumo = pd.DataFrame({
                'Variáveis': [
                    'Valor FOB ↔ Peso Líquido',
                    'Valor FOB ↔ Valor Frete', 
                    'Peso Líquido ↔ Valor Frete',
                    'Valor FOB ↔ Quantidade',
                    'Peso Líquido ↔ Quantidade'
                ],
                'Correlação': [
                    df_filtered['valor_fob'].corr(df_filtered['peso_liquido']),
                    df_filtered['valor_fob'].corr(df_filtered['valor_frete']),
                    df_filtered['peso_liquido'].corr(df_filtered['valor_frete']),
                    df_filtered['valor_fob'].corr(df_filtered['quantidade']),
                    df_filtered['peso_liquido'].corr(df_filtered['quantidade'])
                ],
                'Interpretação': [
                    'Produtos pesados = maior valor' if df_filtered['valor_fob'].corr(df_filtered['peso_liquido']) > 0.3 else 'Relação fraca',
                    'Frete proporcional ao valor' if df_filtered['valor_fob'].corr(df_filtered['valor_frete']) > 0.5 else 'Frete independente do valor',
                    'Frete baseado no peso' if df_filtered['peso_liquido'].corr(df_filtered['valor_frete']) > 0.3 else 'Frete não baseado no peso',
                    'Volume impacta valor' if df_filtered['valor_fob'].corr(df_filtered['quantidade']) > 0.3 else 'Volume não determina valor',
                    'Peso relacionado à quantidade' if df_filtered['peso_liquido'].corr(df_filtered['quantidade']) > 0.3 else 'Peso independente da quantidade'
                ]
            })
            
            # Colorir correlações por intensidade
            def color_correlation(val):
                if abs(val) > 0.7:
                    return 'background-color: #2E8B57; color: white'  # Verde forte
                elif abs(val) > 0.5:
                    return 'background-color: #90EE90; color: black'  # Verde claro
                elif abs(val) > 0.3:
                    return 'background-color: #FFFF99; color: black'  # Amarelo
                else:
                    return 'background-color: #FFB6C1; color: black'  # Rosa claro
            
            styled_df = correlacoes_resumo.style.applymap(color_correlation, subset=['Correlação'])
            st.dataframe(styled_df, use_container_width=True)
        
        # Análise de outliers
        st.markdown("#### 🎯 Análise de Outliers")
        
        outliers_query = """
        SELECT 
            i.VL_FOB,
            i.KG_LIQUIDO,
            i.QT_ESTATISTICA,
            p.NOME_PAIS,
            n.NOME_NCM,
            uf.NOME_UF
        FROM Importacoes i
        JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        JOIN NCM n ON i.COD_NCM = n.COD_NCM
        JOIN UF uf ON i.COD_UF = uf.COD_UF
        ORDER BY i.VL_FOB DESC
        LIMIT 100
        """
        
        df_outliers = fetch_data(outliers_query, conn)
        
        if not df_outliers.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot do valor FOB
                fig_box_valor = px.box(
                    df_outliers,
                    y='VL_FOB',
                    title='📦 Distribuição dos Valores FOB (Top 100)',
                    labels={'VL_FOB': 'Valor FOB (US$)'}
                )
                fig_box_valor.update_layout(height=400)
                st.plotly_chart(fig_box_valor, use_container_width=True)
            
            with col2:
                # Box plot do peso
                fig_box_peso = px.box(
                    df_outliers,
                    y='KG_LIQUIDO',
                    title='⚖️ Distribuição dos Pesos (Top 100)',
                    labels={'KG_LIQUIDO': 'Peso Líquido (kg)'}
                )
                fig_box_peso.update_layout(height=400)
                st.plotly_chart(fig_box_peso, use_container_width=True)
            
            # Top 10 maiores importações
            st.markdown("#### 🏆 Top 10 Maiores Importações por Valor")
            
            df_top_imports = df_outliers.head(10)[['VL_FOB', 'KG_LIQUIDO', 'NOME_PAIS', 
                                                  'NOME_NCM', 'NOME_UF']].copy()
            df_top_imports['VL_FOB'] = df_top_imports['VL_FOB'].apply(lambda x: f"US$ {x:,.2f}")
            df_top_imports['KG_LIQUIDO'] = df_top_imports['KG_LIQUIDO'].apply(lambda x: f"{x:,.2f} kg")
            df_top_imports.columns = ['Valor FOB', 'Peso Líquido', 'País', 'Produto NCM', 'Estado']
            
            st.dataframe(df_top_imports, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px;">
        <p style="margin: 0; color: #666;">
            📊 Dashboard desenvolvido para análise dos dados de importações brasileiras 2024<br>
            🔗 Fonte: Comex Stat - Balança Comercial | 
            👥 Desenvolvido por: Daniel da Cunha Costa, Isaac Reyes Alves de Abreu, Pedro Luiz Silva
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fechar conexão
    conn.close()

if __name__ == "__main__":
    main()