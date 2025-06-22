# 📊 Dashboard de Importações Brasil 2024

## 🎯 Sobre o Projeto

Dashboard interativo desenvolvido em **Streamlit** para análise exploratória dos dados de importações brasileiras por código NCM em 2024. 

**Equipe:**
- Daniel da Cunha Costa - 2024006064
- Isaac Reyes Alves de Abreu - 2025050342  
- Pedro Luiz Silva - 2024006129

## 🚀 Como Executar

### 1. Ativar o ambiente virtual
```bash
# No PowerShell/Terminal
.venv\Scripts\Activate.ps1

# Ou no Bash
source .venv/bin/activate
```

### 2. Executar o dashboard
```bash
# Método 1: Streamlit direto
streamlit run streamlit.py

# Método 2: Usando Python
python -m streamlit run streamlit.py

# Método 3: Script automatizado (Windows)
.\run_dashboard.bat
```

### 3. Acessar o dashboard
- **URL:** http://localhost:8501
- O dashboard abrirá automaticamente no seu navegador

## 📊 Funcionalidades

### 🗂️ Abas de Análise

1. **📅 Análise Temporal**
   - Evolução mensal das importações
   - Análise por trimestres e semestres
   - Métricas: valor, operações, peso, valor médio

2. **🌍 Análise por Países**
   - Top países por valor de importação
   - Heatmap de importações por país/mês
   - Correlação valor vs operações

3. **🏛️ Análise por Estados**
   - Distribuição por UF e regiões
   - Concentração geográfica
   - Top estados importadores

4. **📦 Análise por NCM**
   - Top produtos por valor
   - Análise de densidade de valor
   - Detalhamento dos códigos NCM

5. **🔍 Análise Detalhada**
   - Matriz de correlação
   - Análise de outliers
   - Top maiores importações

### 🎨 Interface

- **Design moderno** com gradientes e cards informativos
- **Visualizações interativas** com Plotly
- **Filtros dinâmicos** na sidebar
- **Cache de dados** para performance otimizada

## 🔧 Tecnologias

- **Python 3.12+**
- **Streamlit** - Framework web
- **Plotly** - Visualizações interativas
- **Pandas** - Manipulação de dados
- **SQLite** - Banco de dados
- **NumPy** - Computação numérica

## 📁 Estrutura do Projeto

```
├── streamlit.py           # Aplicativo principal
├── importacoes_brasil_2024.db  # Banco de dados SQLite
├── migration.ipynb       # Script de migração dos dados
├── .streamlit/           # Configurações do Streamlit
│   └── config.toml
├── run_dashboard.bat     # Script de execução (Windows)
└── README.md            # Este arquivo
```

## 📈 Dados

- **Fonte:** [Comex Stat - Balança Comercial](https://balanca.economia.gov.br/)
- **Período:** Janeiro a Dezembro de 2024
- **Volume:** ~105 MB de dados estruturados

## 🛠️ Solução de Problemas

### Erro de conexão com banco
```
❌ Não foi possível conectar ao banco de dados
```
**Solução:** Execute primeiro o `migration.ipynb` para criar o banco `importacoes_brasil_2024.db`

### Streamlit não encontrado
```
'streamlit' is not recognized as an internal or external command
```
**Solução:** 
1. Ative o ambiente virtual: `.venv\Scripts\Activate.ps1`
2. Use: `python -m streamlit run streamlit.py`

### Porta em uso
```
Port 8501 is already in use
```
**Solução:** 
1. Pare outros processos Streamlit (Ctrl+C)
2. Ou use outra porta: `streamlit run streamlit.py --server.port 8502`

## 📝 Licença

Projeto acadêmico - Disciplina de Introdução a Banco de Dados (IBD)
Dados de domínio público (Governo Federal - Comex Stat)