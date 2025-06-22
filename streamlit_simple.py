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
    st.markdown("## 📈 Visão Geral")    # Construir filtros SQL simples
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
    
    # Debug SQL
    st.write(f"**Debug SQL:** `{sql_filters if sql_filters else 'Sem filtros'}`")
    
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
    
    st.markdown("---")    # Tabs simplificadas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise Temporal", "🌍 Análise por Países", "🏛️ Análise por Estados", "📦 Análise por NCM"])
    
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
        ORDER BY m.COD_MES
        """
        
        st.write("**Query Temporal:**")
        st.code(temporal_query)
        
        df_temporal = fetch_data(temporal_query)
        
        # Debug
        st.write(f"📊 **Debug Temporal:** {len(df_temporal)} registros encontrados")
        
        if not df_temporal.empty:
            st.write("**Dados encontrados:**")
            st.dataframe(df_temporal)
            
            # Gráfico simples de valor total
            fig = px.line(df_temporal, x='NOME_MES', y='valor_total', 
                         title='Valor Total das Importações por Mês',
                         labels={'valor_total': 'Valor Total (US$ FOB)', 'NOME_MES': 'Mês'})
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico de operações
            fig2 = px.bar(df_temporal, x='NOME_MES', y='total_operacoes',
                         title='Número de Operações por Mês',
                         labels={'total_operacoes': 'Total de Operações', 'NOME_MES': 'Mês'})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum dado encontrado para o período selecionado")
    
    with tab2:
        st.markdown("### 🌍 Principais Países de Origem")
          # Query para países com filtros (limitando a top 10)
        paises_query = f"""
        SELECT 
            p.NOME_PAIS,
            COUNT(*) as total_operacoes,
            SUM(i.VL_FOB) as valor_total,
            SUM(i.KG_LIQUIDO) as peso_total,
            AVG(i.VL_FOB) as valor_medio
        FROM Importacoes i
        JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
        LEFT JOIN UF uf ON i.COD_UF = uf.COD_UF
        {sql_filters}
        GROUP BY p.COD_PAIS, p.NOME_PAIS
        ORDER BY valor_total DESC
        LIMIT 10
        """
        
        st.write("**Query Países:**")
        st.code(paises_query)
        
        df_paises = fetch_data(paises_query)
        
        # Debug
        st.write(f"🌍 **Debug Países:** {len(df_paises)} registros encontrados")
        
        if not df_paises.empty:
            st.write("**Top 10 Países:**")
            st.dataframe(df_paises)
            
            # Gráfico de barras horizontal
            fig = px.bar(df_paises, x='valor_total', y='NOME_PAIS', 
                        orientation='h',
                        title='Top 10 Países por Valor Total de Importações',
                        labels={'valor_total': 'Valor Total (US$ FOB)', 'NOME_PAIS': 'País'})
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
              # Gráfico de pizza
            fig2 = px.pie(df_paises, values='valor_total', names='NOME_PAIS',
                         title='Distribuição do Valor Total por País (Top 10)')
            st.plotly_chart(fig2, use_container_width=True)
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
        LIMIT 15
        """
        
        st.write("**Query Estados:**")
        st.code(estados_query)
        
        df_estados = fetch_data(estados_query)
        
        # Debug
        st.write(f"🏛️ **Debug Estados:** {len(df_estados)} registros encontrados")
        
        if not df_estados.empty:
            st.write("**Top 15 Estados:**")
            st.dataframe(df_estados)
            
            # Gráfico de barras
            fig = px.bar(df_estados, x='SIGLA_UF', y='valor_total', 
                        title='Top 15 Estados por Valor Total de Importações',
                        labels={'valor_total': 'Valor Total (US$ FOB)', 'SIGLA_UF': 'Estado'},
                        hover_data=['NOME_UF', 'total_operacoes'])
            st.plotly_chart(fig, use_container_width=True)
              # Gráfico de pizza para top 10
            top_10_estados = df_estados.head(10)
            fig2 = px.pie(top_10_estados, values='valor_total', names='SIGLA_UF',
                         title='Distribuição do Valor Total por Estado (Top 10)')
            st.plotly_chart(fig2, use_container_width=True)
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
        LIMIT 15
        """
        
        st.write("**Query NCMs:**")
        st.code(ncm_query)
        
        df_ncm = fetch_data(ncm_query)
        
        # Debug
        st.write(f"📦 **Debug NCMs:** {len(df_ncm)} registros encontrados")
        
        if not df_ncm.empty:
            st.write("**Top 15 NCMs:**")
            
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

if __name__ == "__main__":
    main()
