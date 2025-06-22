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

def build_sql_filters(periodo_selecionado, regiao_selecionada, valor_minimo):
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
    
    # Retornar filtros
    if filters:
        return "WHERE " + " AND ".join(filters)
    return ""

def get_basic_stats(sql_filters=""):
    """Retorna estatísticas básicas do banco com filtros opcionais"""
    try:
        conn = sqlite3.connect('importacoes_brasil_2024.db', check_same_thread=False)
        stats = {}
        
        # Base das queries (precisa do LEFT JOIN para região)
        base_from = "FROM Importacoes i LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF"
        
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
      # Estatísticas gerais
    st.markdown("## 📈 Visão Geral")
    
    # Construir filtros SQL simples
    sql_filters = build_sql_filters(periodo_selecionado, regiao_selecionada, valor_minimo)
    
    # Mostrar filtros aplicados
    filtros_ativos = []
    if periodo_selecionado != "Ano Completo (2024)":
        filtros_ativos.append(periodo_selecionado)
    if regiao_selecionada != "Brasil Completo":
        filtros_ativos.append(regiao_selecionada)
    if valor_minimo != "Todos os valores":
        filtros_ativos.append(valor_minimo)
    
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
        st.markdown("### 📅 Evolução das Importações ao Longo do Ano")
          # Query para dados temporais com filtros
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
        {sql_filters}
        GROUP BY m.COD_MES, m.NOME_MES
        ORDER BY m.COD_MES        """
        
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
        st.markdown("### 🌍 Principais Países de Origem")          # Query para países com filtros (expandida)
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
        ORDER BY valor_total DESC        LIMIT 15
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
        {sql_filters}
        GROUP BY uf.COD_UF, uf.NOME_UF, uf.SIGLA_UF
        ORDER BY valor_total DESC
        LIMIT 15        """
        
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
        {sql_filters}
        GROUP BY n.COD_NCM, n.NOME_NCM, u.NOME_UNID, u.SIGLA_UNID
        ORDER BY valor_total DESC
        LIMIT 15        """
        
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
        st.markdown("### 🔍 Análise Detalhada e Correlações")
        
        # Análise de correlações entre variáveis numéricas com filtros
        correlacao_query = f"""
        SELECT 
            VL_FOB as valor_fob,
            KG_LIQUIDO as peso_liquido,
            VL_FRETE as valor_frete,
            VL_SEGURO as valor_seguro,
            QT_ESTATISTICA as quantidade
        FROM Importacoes i
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        {sql_filters if sql_filters else ''}
        {' AND ' if sql_filters else 'WHERE '} VL_FOB > 0 AND KG_LIQUIDO > 0
        LIMIT 10000
        """
        
        df_corr = fetch_data(correlacao_query)
        
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
                (df_analysis['percentual_frete'] <= 50)
            ].sample(n=min(2000, len(df_analysis)))
            
            # Análise 1: Valor FOB vs Peso Líquido
            st.markdown("##### 💰 Análise: Valor FOB vs Peso Líquido")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig_valor_peso = px.scatter(
                    df_filtered.sample(n=min(1000, len(df_filtered))),
                    x='peso_liquido',
                    y='valor_fob',
                    title='Relação entre Valor FOB e Peso Líquido',
                    labels={'peso_liquido': 'Peso Líquido (kg)', 'valor_fob': 'Valor FOB (US$)'},
                    opacity=0.6
                )
                st.plotly_chart(fig_valor_peso, use_container_width=True)
            
            with col2:
                correlacao_valor_peso = df_filtered['valor_fob'].corr(df_filtered['peso_liquido'])
                st.metric("Correlação", f"{correlacao_valor_peso:.3f}")
                if correlacao_valor_peso > 0.3:
                    st.success("✅ Correlação positiva moderada")
                elif correlacao_valor_peso < -0.3:
                    st.error("❌ Correlação negativa moderada")
                else:
                    st.warning("⚠️ Correlação fraca")
            
            # Análise 2: Frete vs Valor FOB
            st.markdown("##### 🚢 Análise: Custo de Frete vs Valor FOB")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig_frete_valor = px.scatter(
                    df_filtered.sample(n=min(1000, len(df_filtered))),
                    x='valor_fob',
                    y='valor_frete',
                    title='Relação entre Valor FOB e Custo de Frete',
                    labels={'valor_fob': 'Valor FOB (US$)', 'valor_frete': 'Valor Frete (US$)'},
                    opacity=0.6
                )
                st.plotly_chart(fig_frete_valor, use_container_width=True)
            
            with col2:
                correlacao_frete = df_filtered['valor_fob'].corr(df_filtered['valor_frete'])
                st.metric("Correlação", f"{correlacao_frete:.3f}")
                if correlacao_frete > 0.5:
                    st.success("✅ Frete proporcional ao valor")
                else:
                    st.warning("⚠️ Frete independente do valor")
            
            # Análise 3: Distribuição do Percentual de Frete
            st.markdown("##### 📊 Distribuição dos Custos de Frete")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist_frete = px.histogram(
                    df_filtered,
                    x='percentual_frete',
                    nbins=30,
                    title='Distribuição do Percentual de Frete',
                    labels={'percentual_frete': 'Percentual do Frete (%)', 'count': 'Frequência'}
                )
                st.plotly_chart(fig_hist_frete, use_container_width=True)
            
            with col2:
                # Estatísticas do frete
                st.markdown("**Estatísticas do Frete:**")
                st.write(f"- Média: {df_filtered['percentual_frete'].mean():.1f}%")
                st.write(f"- Mediana: {df_filtered['percentual_frete'].median():.1f}%")
                st.write(f"- Desvio Padrão: {df_filtered['percentual_frete'].std():.1f}%")
                st.write(f"- Máximo: {df_filtered['percentual_frete'].max():.1f}%")
            
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
            st.dataframe(correlacoes_resumo, use_container_width=True)
        
        # Análise de outliers
        st.markdown("#### 🎯 Análise de Outliers")
        
        outliers_query = f"""
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
        {sql_filters}
        ORDER BY i.VL_FOB DESC
        LIMIT 100
        """
        
        df_outliers = fetch_data(outliers_query)
        
        if not df_outliers.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot dos valores
                fig_box = px.box(df_outliers.head(50), y='VL_FOB',
                               title='📦 Distribuição dos Maiores Valores FOB')
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col2:
                # Scatter plot: Valor vs Peso dos outliers
                fig_outlier_scatter = px.scatter(df_outliers.head(30), 
                                               x='KG_LIQUIDO', y='VL_FOB',
                                               hover_name='NOME_PAIS',
                                               title='💎 Outliers: Valor vs Peso')
                st.plotly_chart(fig_outlier_scatter, use_container_width=True)
            
            # Top 10 maiores importações
            st.markdown("#### 🏆 Top 10 Maiores Importações por Valor")
            
            df_top_imports = df_outliers.head(10)[['VL_FOB', 'KG_LIQUIDO', 'NOME_PAIS', 
                                                  'NOME_NCM', 'NOME_UF']].copy()
            df_top_imports['VL_FOB'] = df_top_imports['VL_FOB'].apply(lambda x: f"US$ {x:,.2f}")
            df_top_imports['KG_LIQUIDO'] = df_top_imports['KG_LIQUIDO'].apply(lambda x: f"{x:,.2f} kg")
            df_top_imports['NOME_NCM'] = df_top_imports['NOME_NCM'].apply(lambda x: x[:60] + '...' if len(x) > 60 else x)
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

if __name__ == "__main__":
    main()
