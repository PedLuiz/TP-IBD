import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

# Configurações
warnings.filterwarnings('ignore')
st.set_page_config(
    page_title="Dashboard de Importações Brasil 2024",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
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
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
def get_connection():
    """Conecta ao banco SQLite"""
    try:
        conn = sqlite3.connect('importacoes_brasil_2024.db', check_same_thread=False)
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def fetch_data(query):
    """Executa query e retorna DataFrame"""
    try:
        conn = sqlite3.connect('importacoes_brasil_2024.db', check_same_thread=False)
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        st.error(f"Erro ao executar query: {e}")
        return pd.DataFrame()

def build_sql_filters(periodo_selecionado, regiao_selecionada, valor_minimo, pais_selecionado):
    """Constrói filtros SQL baseados nas seleções do usuário"""
    filters = []
    
    # Filtro de período
    if periodo_selecionado == "1º Semestre":
        filters.append("i.COD_MES <= 6")
    elif periodo_selecionado == "2º Semestre":
        filters.append("i.COD_MES > 6")
    elif periodo_selecionado == "1º Trimestre":
        filters.append("i.COD_MES <= 3")
    elif periodo_selecionado == "2º Trimestre":
        filters.append("i.COD_MES BETWEEN 4 AND 6")
    elif periodo_selecionado == "3º Trimestre":
        filters.append("i.COD_MES BETWEEN 7 AND 9")
    elif periodo_selecionado == "4º Trimestre":
        filters.append("i.COD_MES >= 10")
    
    # Filtro de região
    if regiao_selecionada != "Brasil Completo":
        regioes_map = {
            "Sudeste": ["SP", "RJ", "MG", "ES"],
            "Sul": ["RS", "SC", "PR"], 
            "Nordeste": ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "SE", "PI"],
            "Norte": ["AM", "PA", "RO", "AC", "RR", "AP", "TO"],
            "Centro-Oeste": ["GO", "MT", "MS", "DF"]
        }
        if regiao_selecionada in regioes_map:
            ufs = regioes_map[regiao_selecionada]
            ufs_str = "', '".join(ufs)
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
    
    # Filtro de país
    if pais_selecionado != "Todos os países":
        # Escapar aspas simples no nome do país
        pais_escaped = pais_selecionado.replace("'", "''")
        filters.append(f"p.NOME_PAIS = '{pais_escaped}'")
    
    # Retornar filtros
    if filters:
        return "WHERE " + " AND ".join(filters)
    return ""

def get_basic_stats(sql_filters=""):
    """Retorna estatísticas básicas do banco com filtros opcionais"""
    try:
        conn = sqlite3.connect('importacoes_brasil_2024.db', check_same_thread=False)
        stats = {}
          # Base das queries (precisa do LEFT JOIN para região e país)
        base_from = "FROM Importacoes i LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS"
        
        # Total de importações
        total_query = f"SELECT COUNT(*) as total {base_from} {sql_filters}"
        result = pd.read_sql_query(total_query, conn)
        stats['total_imports'] = result['total'].iloc[0] if not result.empty else 0
        
        # Valor total FOB
        value_query = f"SELECT SUM(i.VL_FOB) as total_value {base_from} {sql_filters}"
        result = pd.read_sql_query(value_query, conn)
        stats['total_value'] = result['total_value'].iloc[0] if not result.empty and result['total_value'].iloc[0] is not None else 0
        
        # Países únicos
        countries_query = f"SELECT COUNT(DISTINCT i.COD_PAIS) as countries {base_from} {sql_filters}"
        result = pd.read_sql_query(countries_query, conn)
        stats['unique_countries'] = result['countries'].iloc[0] if not result.empty else 0
        
        # NCMs únicos
        ncm_query = f"SELECT COUNT(DISTINCT i.COD_NCM) as ncms {base_from} {sql_filters}"
        result = pd.read_sql_query(ncm_query, conn)
        stats['unique_ncms'] = result['ncms'].iloc[0] if not result.empty else 0
        
        conn.close()
        return stats
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return {'total_imports': 0, 'total_value': 0, 'unique_countries': 0, 'unique_ncms': 0}

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
    
    # Conectar ao banco para teste
    conn = get_connection()
    if conn is None:
        st.error("❌ Não foi possível conectar ao banco de dados. Verifique se o arquivo 'importacoes_brasil_2024.db' existe.")
        return
    conn.close()
    
    # Sidebar para filtros
    st.sidebar.markdown('<div class="sidebar-header">🔍 Filtros de Análise</div>', 
                       unsafe_allow_html=True)
      # Filtro de período simples
    periodo_selecionado = st.sidebar.selectbox(
        "📅 Período de Análise",
        options=["Ano Completo (2024)", "1º Semestre", "2º Semestre", "1º Trimestre", "2º Trimestre", "3º Trimestre", "4º Trimestre"],
        index=0
    )
      # Filtro de região
    regiao_selecionada = st.sidebar.selectbox(
        "🗺️ Região do Brasil",
        options=["Brasil Completo", "Sudeste", "Sul", "Nordeste", "Norte", "Centro-Oeste"],
        index=0
    )
      # Filtro de valor mínimo
    valor_minimo = st.sidebar.selectbox(
        "💰 Valor Mínimo da Operação",
        options=["Todos os valores", "Acima de US$ 1.000", "Acima de US$ 10.000", "Acima de US$ 100.000", "Acima de US$ 1.000.000"],
        index=0,
        help="Filtrar operações por valor mínimo para focar em grandes importações"
    )
    
    # Filtro de países (carregar dinamicamente)
    @st.cache_data
    def get_countries():
        query = "SELECT DISTINCT p.NOME_PAIS FROM Pais p JOIN Importacoes i ON p.COD_PAIS = i.COD_PAIS ORDER BY p.NOME_PAIS"
        return fetch_data(query)
    
    df_countries = get_countries()
    countries_list = ["Todos os países"] + df_countries['NOME_PAIS'].tolist() if not df_countries.empty else ["Todos os países"]
    
    pais_selecionado = st.sidebar.selectbox(
        "🌍 País de Origem",
        options=countries_list,
        index=0,
        help="Filtrar importações por país de origem específico"
    )
      # Estatísticas gerais
    st.markdown("## 📈 Visão Geral")
      # Construir filtros SQL simples
    sql_filters = build_sql_filters(periodo_selecionado, regiao_selecionada, valor_minimo, pais_selecionado)
    
    # Mostrar filtros aplicados
    filtros_ativos = []
    if periodo_selecionado != "Ano Completo (2024)":
        filtros_ativos.append(periodo_selecionado)
    if regiao_selecionada != "Brasil Completo":
        filtros_ativos.append(regiao_selecionada)
    if valor_minimo != "Todos os valores":
        filtros_ativos.append(valor_minimo)
    if pais_selecionado != "Todos os países":
        filtros_ativos.append(f"País: {pais_selecionado}")
    
    if filtros_ativos:
        st.info(f"🔍 **Filtros Aplicados:** {' • '.join(filtros_ativos)}")
    
    stats = get_basic_stats(sql_filters)
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
    
    st.markdown("---")    # Tabs completas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Análise Temporal", 
        "🌍 Análise por Países", 
        "🏛️ Análise por Estados",
        "📦 Análise por NCM",
        "🔍 Análise Detalhada"
    ])
    
    with tab1:
        st.markdown("### 📅 Evolução das Importações ao Longo do Ano")        # Query para dados temporais com filtros
        temporal_query = f"""
        SELECT 
            m.NOME_MES,
            m.COD_MES,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN Mes m ON i.COD_MES = m.COD_MES
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        {sql_filters}
        GROUP BY m.COD_MES, m.NOME_MES
        ORDER BY m.COD_MES
        """
        
        df_temporal = fetch_data(temporal_query)
        
        if not df_temporal.empty:
            st.markdown("#### 📈 Dados Mensais")
              # Exibir resumo dos dados
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Meses com Dados", len(df_temporal))
            with col2:
                st.metric("Valor Total Período", f"US$ {df_temporal['valor_total'].sum():,.0f}")
            
            st.markdown("#### 📊 Visualizações")
            
            # Gráfico principal com subplots
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
                title_text="📈 Análise Temporal Completa das Importações"
            )
            
            # Rotacionar labels do eixo x
            fig_temporal.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig_temporal, use_container_width=True)
            
            # Análise de sazonalidade
            st.markdown("#### 📅 Análise de Sazonalidade")
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
                semestre_data = df_temporal.groupby('semestre').agg({
                    'valor_total': 'sum'
                }).reset_index()
                semestre_data['semestre_nome'] = semestre_data['semestre'].map({1: '1º Semestre', 2: '2º Semestre'})
                
                fig_semestre = px.pie(
                    semestre_data,
                    values='valor_total',
                    names='semestre_nome',
                    title='📊 Distribuição por Semestre'
                )
                fig_semestre.update_layout(height=400)
                st.plotly_chart(fig_semestre, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum dado encontrado para o período selecionado")
    
    with tab2:
        st.markdown("### 🌍 Principais Países de Origem")        # Query para países com filtros (expandida)
        paises_query = f"""
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
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        {sql_filters}
        GROUP BY p.COD_PAIS, p.NOME_PAIS
        ORDER BY valor_total DESC
        LIMIT 15
        """
        
        df_paises = fetch_data(paises_query)
        
        if not df_paises.empty:
            st.markdown("#### 🏆 Top 15 Países por Valor de Importação")
            
            # Métricas resumo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Países Representados", len(df_paises))
            with col2:
                st.metric("Maior Importador", df_paises.iloc[0]['NOME_PAIS'])
            with col3:
                st.metric("Valor do Líder", f"US$ {df_paises.iloc[0]['valor_total']:,.0f}")
            
            st.markdown("#### 📊 Visualizações")
            
            # Gráfico de barras horizontal
            fig = px.bar(df_paises.head(10), x='valor_total', y='NOME_PAIS', 
                        orientation='h',
                        title='Top 10 Países por Valor Total de Importações',
                        labels={'valor_total': 'Valor Total (US$ FOB)', 'NOME_PAIS': 'País'})
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Análises adicionais
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza
                fig2 = px.pie(df_paises.head(8), values='valor_total', names='NOME_PAIS',
                             title='Distribuição do Valor Total por País (Top 8)')
                st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                # Scatter: Valor vs Número de Operações
                fig_scatter = px.scatter(df_paises, x='total_operacoes', y='valor_total',
                                       size='peso_total', color='valor_medio',
                                       hover_name='NOME_PAIS',
                                       title='Valor vs Operações por País',
                                       labels={'total_operacoes': 'Total de Operações', 
                                              'valor_total': 'Valor Total (US$)',
                                              'valor_medio': 'Valor Médio'})
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Mapa de calor - Países por mês (apenas se não há filtro de período específico)
            if periodo_selecionado == "Ano Completo (2024)":
                st.markdown("#### 🗓️ Análise Temporal por País")
                
                paises_mes_query = f"""
                SELECT 
                    p.NOME_PAIS,
                    m.NOME_MES,
                    m.COD_MES,
                    SUM(i.VL_FOB) as valor_total
                FROM Importacoes i
                JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
                JOIN Mes m ON i.COD_MES = m.COD_MES
                LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
                WHERE p.NOME_PAIS IN ({','.join([f"'{pais}'" for pais in df_paises.head(8)['NOME_PAIS']])})
                {' AND ' + sql_filters.replace('WHERE ', '') if sql_filters else ''}
                GROUP BY p.NOME_PAIS, m.NOME_MES, m.COD_MES
                ORDER BY m.COD_MES
                """
                
                df_heatmap = fetch_data(paises_mes_query)
                
                if not df_heatmap.empty:
                    # Criar pivot table para heatmap
                    pivot_data = df_heatmap.pivot(index='NOME_PAIS', columns='NOME_MES', values='valor_total')
                    pivot_data = pivot_data.fillna(0)
                    
                    # Heatmap
                    fig_heatmap = px.imshow(
                        pivot_data.values,
                        x=pivot_data.columns,
                        y=pivot_data.index,
                        title='🌡️ Mapa de Calor: Valor de Importações por País e Mês',
                        color_continuous_scale='Blues',
                        aspect='auto'
                    )
                    fig_heatmap.update_layout(height=500)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum dado encontrado para o período/região selecionados")
    
    with tab3:
        st.markdown("### 🏛️ Análise por Estados Brasileiros")
          # Query para estados com filtros (limitando a top 15)
        estados_query = f"""
        SELECT 
            uf.NOME_UF,
            uf.SIGLA_UF,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN UF uf ON i.COD_UF = uf.COD_UF
        LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        {sql_filters}
        GROUP BY uf.COD_UF, uf.NOME_UF, uf.SIGLA_UF
        ORDER BY valor_total DESC
        LIMIT 15
        """
        
        df_estados = fetch_data(estados_query)
        
        if not df_estados.empty:
            st.markdown("#### 🏛️ Top 15 Estados por Valor de Importação")
            
            # Métricas resumo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estados Representados", len(df_estados))
            with col2:
                st.metric("Estado Líder", f"{df_estados.iloc[0]['SIGLA_UF']} - {df_estados.iloc[0]['NOME_UF']}")
            with col3:
                st.metric("Valor do Líder", f"US$ {df_estados.iloc[0]['valor_total']:,.0f}")
            
            st.markdown("#### 📊 Visualizações")
            
            # Gráfico de barras
            fig = px.bar(df_estados, x='SIGLA_UF', y='valor_total', 
                        title='Top 15 Estados por Valor Total de Importações',
                        labels={'valor_total': 'Valor Total (US$ FOB)', 'SIGLA_UF': 'Estado'},
                        hover_data=['NOME_UF', 'total_operacoes'])
            st.plotly_chart(fig, use_container_width=True)            # Gráfico de pizza para top 10
            top_10_estados = df_estados.head(10)
            fig2 = px.pie(top_10_estados, values='valor_total', names='SIGLA_UF',
                         title='Distribuição do Valor Total por Estado (Top 10)')
            st.plotly_chart(fig2, use_container_width=True)
            
            # Análise de concentração por região
            st.markdown("#### 📍 Análise Regional")
            
            # Mapeamento de regiões
            regioes = {
                'SP': 'Sudeste', 'RJ': 'Sudeste', 'MG': 'Sudeste', 'ES': 'Sudeste',
                'RS': 'Sul', 'SC': 'Sul', 'PR': 'Sul',
                'BA': 'Nordeste', 'PE': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste',
                'PB': 'Nordeste', 'RN': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'PI': 'Nordeste',
                'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'DF': 'Centro-Oeste',
                'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'AC': 'Norte', 'RR': 'Norte', 'AP': 'Norte', 'TO': 'Norte'
            }
            
            df_estados['REGIAO'] = df_estados['SIGLA_UF'].map(regioes)
            df_regioes = df_estados.groupby('REGIAO').agg({
                'valor_total': 'sum',
                'total_operacoes': 'sum',
                'peso_total': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_regioes = px.bar(df_regioes, x='REGIAO', y='valor_total',
                                   title='💰 Valor Total por Região',
                                   labels={'valor_total': 'Valor Total (US$)', 'REGIAO': 'Região'})
                fig_regioes.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_regioes, use_container_width=True)
            
            with col2:
                fig_pie_regioes = px.pie(df_regioes, values='valor_total', names='REGIAO',
                                       title='📊 Distribuição por Região')
                st.plotly_chart(fig_pie_regioes, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum dado encontrado para o período/região selecionados")
    
    with tab4:
        st.markdown("### 📦 Análise por Código NCM")
          # Query para NCMs com filtros (limitando a top 15)
        ncm_query = f"""
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
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        {sql_filters}
        GROUP BY n.COD_NCM, n.NOME_NCM, u.NOME_UNID, u.SIGLA_UNID
        ORDER BY valor_total DESC
        LIMIT 15
        """
        
        df_ncm = fetch_data(ncm_query)
        
        if not df_ncm.empty:
            st.markdown("#### 📦 Top 15 Produtos por Código NCM")
            
            # Métricas resumo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("NCMs Representados", len(df_ncm))
            with col2:
                produto_lider = df_ncm.iloc[0]['NOME_NCM'][:40] + "..." if len(df_ncm.iloc[0]['NOME_NCM']) > 40 else df_ncm.iloc[0]['NOME_NCM']
                st.metric("Produto Líder", produto_lider)
            with col3:
                st.metric("Valor do Líder", f"US$ {df_ncm.iloc[0]['valor_total']:,.0f}")
            
            st.markdown("#### 📋 Dados Detalhados")
            
            # Truncar nomes muito longos para visualização
            df_ncm['NOME_NCM_SHORT'] = df_ncm['NOME_NCM'].apply(
                lambda x: x[:50] + '...' if len(str(x)) > 50 else x
            )
              # Mostrar tabela
            df_display = df_ncm[['COD_NCM', 'NOME_NCM_SHORT', 'SIGLA_UNID', 'total_operacoes', 'valor_total', 'valor_medio']].copy()
            df_display['valor_total'] = df_display['valor_total'].apply(lambda x: f"US$ {x:,.0f}")
            df_display['valor_medio'] = df_display['valor_medio'].apply(lambda x: f"US$ {x:,.0f}")
            df_display.columns = ['Código NCM', 'Produto', 'Unidade', 'Operações', 'Valor Total', 'Valor Médio']
            st.dataframe(df_display, use_container_width=True)
            
            st.markdown("#### 📊 Visualizações")
            
            # Gráfico de barras horizontal
            fig = px.bar(df_ncm.head(10), x='valor_total', y='NOME_NCM_SHORT', 
                        orientation='h',
                        title='Top 10 NCMs por Valor Total de Importações',
                        labels={'valor_total': 'Valor Total (US$ FOB)', 'NOME_NCM_SHORT': 'Produto NCM'})
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Scatter plot - Valor vs Quantidade
            col1, col2 = st.columns(2)
            
            with col1:
                fig_scatter = px.scatter(df_ncm.head(15), x='quantidade_total', y='valor_total',
                                       size='total_operacoes', color='valor_medio',
                                       hover_name='NOME_NCM_SHORT',
                                       title='Valor vs Quantidade por NCM',
                                       labels={'quantidade_total': 'Quantidade Total', 
                                              'valor_total': 'Valor Total (US$)',
                                              'valor_medio': 'Valor Médio (US$)'})
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col2:
                # Histograma de valor médio
                fig_hist = px.histogram(df_ncm, x='valor_medio', nbins=10,
                                       title='Distribuição do Valor Médio por Operação',
                                       labels={'valor_medio': 'Valor Médio (US$)', 'count': 'Frequência'})
                st.plotly_chart(fig_hist, use_container_width=True)        
        else:
            st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados")

    with tab5:
        st.markdown("### 🔍 Análise Detalhada e Insights")
        
        # Análise 1: Eficiência Comercial
        st.markdown("#### 💡 Análise de Eficiência Comercial")
        
        eficiencia_query = f"""
        SELECT 
            p.NOME_PAIS,
            COUNT(*) as num_operacoes,
            SUM(i.VL_FOB) as valor_total,
            AVG(i.VL_FOB) as valor_medio_operacao,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB / NULLIF(i.KG_LIQUIDO, 0)) as valor_por_kg
        FROM Importacoes i
        JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        {sql_filters if sql_filters else ''}
        {' AND ' if sql_filters else 'WHERE '} i.KG_LIQUIDO > 0 AND i.VL_FOB > 0
        GROUP BY p.COD_PAIS, p.NOME_PAIS
        HAVING COUNT(*) >= 10
        ORDER BY valor_total DESC
        LIMIT 15
        """
        
        df_eficiencia = fetch_data(eficiencia_query)
        
        if not df_eficiencia.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de bolhas: Valor médio vs Valor por kg
                fig_eficiencia = px.scatter(
                    df_eficiencia, 
                    x='valor_medio_operacao', 
                    y='valor_por_kg',
                    size='num_operacoes',
                    color='valor_total',
                    hover_name='NOME_PAIS',
                    title='💰 Eficiência: Valor Médio vs Valor por Kg',
                    labels={
                        'valor_medio_operacao': 'Valor Médio por Operação (US$)',
                        'valor_por_kg': 'Valor por Kg (US$/kg)',
                        'num_operacoes': 'Número de Operações'
                    },
                    color_continuous_scale='Viridis'
                )
                fig_eficiencia.update_layout(height=500)
                st.plotly_chart(fig_eficiencia, use_container_width=True)
            
            with col2:
                # Ranking de eficiência (valor por kg)
                df_top_efficiency = df_eficiencia.nlargest(10, 'valor_por_kg')
                
                fig_ranking = px.bar(
                    df_top_efficiency,
                    x='valor_por_kg',
                    y='NOME_PAIS',
                    orientation='h',
                    title='🏆 Top 10 Países - Maior Valor por Kg',
                    labels={'valor_por_kg': 'Valor por Kg (US$/kg)', 'NOME_PAIS': 'País'},
                    color='valor_por_kg',
                    color_continuous_scale='Blues'
                )
                fig_ranking.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                st.plotly_chart(fig_ranking, use_container_width=True)
        
        # Análise 2: Padrões Sazonais por Categoria
        st.markdown("#### 📅 Análise de Padrões Sazonais")
        
        if periodo_selecionado == "Ano Completo (2024)":
            sazonalidade_query = f"""
            SELECT 
                m.NOME_MES,
                m.COD_MES,
                CASE 
                    WHEN n.COD_NCM LIKE '01%' OR n.COD_NCM LIKE '02%' OR n.COD_NCM LIKE '03%' OR n.COD_NCM LIKE '04%' OR n.COD_NCM LIKE '05%' THEN 'Alimentos e Animais'
                    WHEN n.COD_NCM LIKE '84%' OR n.COD_NCM LIKE '85%' THEN 'Máquinas e Equipamentos'
                    WHEN n.COD_NCM LIKE '87%' THEN 'Veículos'
                    WHEN n.COD_NCM LIKE '27%' THEN 'Combustíveis'
                    WHEN n.COD_NCM LIKE '72%' OR n.COD_NCM LIKE '73%' THEN 'Metais'
                    ELSE 'Outros'
                END as categoria,
                SUM(i.VL_FOB) as valor_total
            FROM Importacoes i
            JOIN Mes m ON i.COD_MES = m.COD_MES
            JOIN NCM n ON i.COD_NCM = n.COD_NCM
            LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
            LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
            {sql_filters if sql_filters else ''}
            GROUP BY m.COD_MES, m.NOME_MES, categoria
            ORDER BY m.COD_MES, valor_total DESC
            """
            
            df_sazonalidade = fetch_data(sazonalidade_query)
            
            if not df_sazonalidade.empty:
                # Gráfico de linha por categoria
                fig_sazon = px.line(
                    df_sazonalidade,
                    x='NOME_MES',
                    y='valor_total',
                    color='categoria',
                    title='📈 Sazonalidade por Categoria de Produtos',
                    labels={'valor_total': 'Valor Total (US$)', 'NOME_MES': 'Mês'},
                    markers=True
                )
                fig_sazon.update_layout(height=500)
                st.plotly_chart(fig_sazon, use_container_width=True)
        else:
            st.info("📌 A análise de sazonalidade está disponível apenas para 'Ano Completo (2024)'")
        
        # Análise 3: Distribuição de Valores
        st.markdown("#### 📊 Análise de Distribuição de Valores")
        
        distribuicao_query = f"""
        SELECT 
            i.VL_FOB,
            CASE 
                WHEN i.VL_FOB <= 1000 THEN 'Até US$ 1K'
                WHEN i.VL_FOB <= 10000 THEN 'US$ 1K - 10K'
                WHEN i.VL_FOB <= 100000 THEN 'US$ 10K - 100K'
                WHEN i.VL_FOB <= 1000000 THEN 'US$ 100K - 1M'
                ELSE 'Acima de US$ 1M'
            END as faixa_valor
        FROM Importacoes i
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        {sql_filters if sql_filters else ''}
        {' AND ' if sql_filters else 'WHERE '} i.VL_FOB > 0
        """
        
        df_distribuicao = fetch_data(distribuicao_query)
        
        if not df_distribuicao.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Contagem por faixa de valor
                faixa_counts = df_distribuicao['faixa_valor'].value_counts()
                
                fig_counts = px.pie(
                    values=faixa_counts.values,
                    names=faixa_counts.index,
                    title='📋 Distribuição por Faixa de Valor (Quantidade)',
                    hole=0.3
                )
                fig_counts.update_layout(height=400)
                st.plotly_chart(fig_counts, use_container_width=True)
            
            with col2:
                # Soma dos valores por faixa
                faixa_sums = df_distribuicao.groupby('faixa_valor')['VL_FOB'].sum()
                
                fig_sums = px.bar(
                    x=faixa_sums.index,
                    y=faixa_sums.values,
                    title='💰 Valor Total por Faixa',
                    labels={'x': 'Faixa de Valor', 'y': 'Valor Total (US$)'},
                    color=faixa_sums.values,
                    color_continuous_scale='Blues'
                )
                fig_sums.update_layout(height=400, xaxis_tickangle=45)
                st.plotly_chart(fig_sums, use_container_width=True)
        
        # Análise 4: Insights Estatísticos
        st.markdown("#### 🎯 Insights Estatísticos")
        
        insights_query = f"""
        SELECT 
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            AVG(i.VL_FOB) as valor_medio,
            MIN(i.VL_FOB) as valor_minimo,
            MAX(i.VL_FOB) as valor_maximo,
            AVG(i.KG_LIQUIDO) as peso_medio,
            COUNT(DISTINCT i.COD_PAIS) as paises_unicos,
            COUNT(DISTINCT i.COD_NCM) as ncms_unicos,
            COUNT(DISTINCT i.COD_UF) as estados_unicos
        FROM Importacoes i
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        LEFT JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        {sql_filters if sql_filters else ''}
        """
        
        df_insights = fetch_data(insights_query)
        
        if not df_insights.empty and len(df_insights) > 0:
            insight = df_insights.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📊 Valor Médio por Operação",
                    f"US$ {insight['valor_medio']:,.2f}"
                )
                st.metric(
                    "📦 Peso Médio por Operação", 
                    f"{insight['peso_medio']:,.1f} kg"
                )
            
            with col2:
                st.metric(
                    "💰 Maior Importação",
                    f"US$ {insight['valor_maximo']:,.2f}"
                )
                st.metric(
                    "💸 Menor Importação",
                    f"US$ {insight['valor_minimo']:,.2f}"
                )
            
            with col3:
                st.metric(
                    "🌍 Diversidade de Países",
                    f"{insight['paises_unicos']} países"
                )
                st.metric(
                    "📦 Diversidade de Produtos",
                    f"{insight['ncms_unicos']} NCMs"
                )
            
            with col4:
                concentracao_geografica = (insight['estados_unicos'] / 27) * 100  # 27 estados brasileiros
                st.metric(
                    "🏛️ Concentração Geográfica",
                    f"{concentracao_geografica:.1f}% dos estados"
                )
                
                # Calcular concentração de valor (Coeficiente de Gini simplificado)
                if insight['total_operacoes'] > 100:
                    concentracao_valor = (insight['valor_maximo'] / insight['valor_total']) * 100
                    st.metric(
                        "⚖️ Concentração de Valor",
                        f"{concentracao_valor:.2f}%"
                    )
        
        # Resumo dos insights
        st.markdown("#### 📝 Resumo dos Insights")
        
        if not df_insights.empty:
            insight = df_insights.iloc[0]
            
            st.markdown(f"""
            **🔍 Principais Descobertas:**
            
            - **Volume de Negócios**: {insight['total_operacoes']:,} operações totalizando US$ {insight['valor_total']:,.2f}
            - **Ticket Médio**: Operações com valor médio de US$ {insight['valor_medio']:,.2f}
            - **Diversificação**: Importações de {insight['paises_unicos']} países diferentes com {insight['ncms_unicos']} produtos distintos
            - **Abrangência Nacional**: Operações em {insight['estados_unicos']} estados brasileiros ({(insight['estados_unicos']/27)*100:.1f}% do país)
            """)
            
            # Análise de concentração
            if insight['valor_maximo'] / insight['valor_medio'] > 100:
                st.warning("⚠️ **Alta Concentração**: Existe uma grande disparidade entre os valores das operações")
            else:
                st.success("✅ **Distribuição Equilibrada**: Os valores das operações são relativamente homogêneos")
        
        else:
            st.warning("⚠️ Não foi possível gerar insights para os filtros selecionados")
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

if __name__ == "__main__":
    main()
