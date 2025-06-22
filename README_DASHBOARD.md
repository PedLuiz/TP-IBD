# 📊 Dashboard de Importações Brasil 2024

## 🎯 Visão Geral

Este projeto apresenta um dashboard interativo desenvolvido em **Streamlit** para análise exploratória dos dados de importações brasileiras por código NCM em 2024. O dashboard oferece uma interface moderna e intuitiva para visualização e análise dos dados através de múltiplas perspectivas.

## ✨ Características Principais

### 📈 Análises Disponíveis

1. **📅 Análise Temporal**
   - Evolução das importações ao longo do ano
   - Análise por trimestres e semestres  
   - Identificação de padrões sazonais
   - Métricas de valor, operações, peso e valor médio

2. **🌍 Análise por Países**
   - Top países por valor total de importações
   - Análise de correlação valor vs operações
   - Heatmap de importações por país e mês
   - Concentração geográfica das importações

3. **🏛️ Análise por Estados**
   - Distribuição por unidades federativas
   - Análise regional (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
   - Identificação dos principais portos/estados de entrada

4. **📦 Análise por NCM**
   - Top produtos por valor de importação
   - Análise de densidade de valor por produto
   - Correlação entre quantidade e valor
   - Detalhamento dos principais códigos NCM

5. **🔍 Análise Detalhada**
   - Matriz de correlação entre variáveis
   - Análise de outliers e valores extremos
   - Relações entre frete, seguro e valor FOB
   - Top maiores importações individuais

### 🎨 Interface e Experiência

- **Design Moderno**: Interface clean com gradientes e cards informativos
- **Navegação Intuitiva**: Organização em tabs para diferentes análises
- **Visualizações Interativas**: Gráficos Plotly com hover, zoom e pan
- **Filtros Dinâmicos**: Sidebar com filtros por mês, país e estado
- **Responsivo**: Adaptável a diferentes tamanhos de tela
- **Performance**: Cache de dados para carregamento rápido

## 🚀 Como Executar

### Pré-requisitos

1. **Python 3.12+** instalado
2. **Banco de dados SQLite** gerado pelo script `migration.ipynb`
3. **Dependências** instaladas (ver seção abaixo)

### Instalação e Execução

1. **Instalar dependências:**

   ```bash
   # Usando uv (recomendado)
   uv sync
   
   # Ou usando pip
   pip install streamlit pandas plotly numpy sqlite3 seaborn
   ```

2. **Garantir que o banco existe:**

   ```bash
   # Execute o notebook de migração primeiro se necessário
   # O arquivo 'importacoes_brasil_2024.db' deve estar na pasta raiz
   ```

3. **Executar o dashboard:**

   ```bash
   streamlit run streamlit.py
   ```

4. **Acessar no navegador:**
   - O dashboard abrirá automaticamente em `http://localhost:8501`
   - Ou acesse manualmente o endereço mostrado no terminal

## 📊 Dados e Estrutura

### Fonte dos Dados

- **Origem**: [Comex Stat - Balança Comercial](https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_2024.csv)
- **Período**: Janeiro a Dezembro de 2024
- **Tipo**: Dados de importações brasileiras por código NCM

### Estrutura do Banco

O banco SQLite contém as seguintes tabelas principais:

- **Importacoes**: Tabela principal com dados de importação
- **Pais**: Códigos e nomes dos países de origem
- **NCM**: Códigos NCM e descrições dos produtos
- **UF**: Estados brasileiros e regiões
- **Unidade**: Unidades de medida
- **Via**: Vias de transporte
- **URF**: Unidades da Receita Federal
- **Mes**: Meses do ano com informações de trimestre/semestre

## 🔧 Funcionalidades Técnicas

### Otimizações de Performance

- **Cache de dados** com `@st.cache_data`
- **Queries SQL otimizadas** com limitações e índices
- **Lazy loading** de dados conforme necessário
- **Amostragem inteligente** para grandes datasets

### Tratamento de Dados

- **Limpeza automática** de valores nulos e inconsistentes
- **Formatação de números** para melhor legibilidade
- **Truncamento de textos** longos em visualizações
- **Agregações eficientes** no banco SQLite

### Visualizações Avançadas

- **Plotly Express/Graph Objects** para interatividade
- **Subplots coordenados** para análises comparativas
- **Color scales personalizadas** para melhor UX
- **Hover data rica** com informações contextuais

## 👥 Equipe de Desenvolvimento

- **Daniel da Cunha Costa** - 2024006064
- **Isaac Reyes Alves de Abreu** - 2025050342  
- **Pedro Luiz Silva** - 2024006129

## 🤝 Contribuições

Este projeto foi desenvolvido como trabalho acadêmico para a disciplina de Introdução a Banco de Dados (IBD). Sugestões e melhorias são bem-vindas!

## 📄 Licença

Projeto desenvolvido para fins acadêmicos. Dados utilizados são de domínio público (Governo Federal - Comex Stat).

---

**🎯 Objetivo**: Demonstrar competências em análise de dados, visualização interativa e desenvolvimento de dashboards modernos usando tecnologias Python.
