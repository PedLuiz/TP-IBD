-- =====================================================
-- CONSULTAS SQL COMPLETAS DO DASHBOARD DE IMPORTAÇÕES BRASIL 2024
-- =====================================================
-- Arquivo: consultas_raw.sql
-- Descrição: TODAS as consultas SQL extraídas do arquivo streamlit.py
-- Organizadas em três grupos conforme solicitado
-- =====================================================

-- =====================================================
-- GRUPO 1: CONSULTAS DE SELEÇÃO E PROJEÇÃO
-- =====================================================

-- 1.1 Seleção e projeção de meses distintos
SELECT DISTINCT COD_MES, NOME_MES 
FROM Mes 
ORDER BY COD_MES;

-- 1.2 Seleção e projeção de UFs distintas
SELECT DISTINCT COD_UF, NOME_UF 
FROM UF 
ORDER BY NOME_UF;

-- 1.3 Total de importações (estatística básica)
SELECT COUNT(*) as total 
FROM Importacoes;

-- 1.4 Valor total FOB (estatística básica)
SELECT SUM(VL_FOB) as total_value 
FROM Importacoes;

-- 1.5 Países únicos (estatística básica)
SELECT COUNT(DISTINCT COD_PAIS) as countries 
FROM Importacoes;

-- 1.6 NCMs únicos (estatística básica)
SELECT COUNT(DISTINCT COD_NCM) as ncms 
FROM Importacoes;

-- 1.7 Análise de correlações (seleção com WHERE)
SELECT 
    VL_FOB as valor_fob,
    KG_LIQUIDO as peso_liquido,
    VL_FRETE as valor_frete,
    VL_SEGURO as valor_seguro,
    QT_ESTATISTICA as quantidade
FROM Importacoes
WHERE VL_FOB > 0 AND KG_LIQUIDO > 0
LIMIT 10000;

-- =====================================================
-- GRUPO 2: CONSULTAS COM JUNÇÃO DE DUAS RELAÇÕES
-- =====================================================

-- 2.1 Junção Importações e Mês para análise temporal
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
ORDER BY m.COD_MES;

-- 2.2 Junção Importações e País para análise por países
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
LIMIT 20;

-- 2.3 Junção Importações e UF para análise por estados
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
ORDER BY valor_total DESC;

-- 2.4 Top países por valor total (para filtros)
SELECT p.COD_PAIS, p.NOME_PAIS, SUM(i.VL_FOB) as total_value
FROM Importacoes i
JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
GROUP BY p.COD_PAIS, p.NOME_PAIS
ORDER BY total_value DESC
LIMIT 20;

-- =====================================================
-- GRUPO 3: CONSULTAS COM JUNÇÃO DE TRÊS OU MAIS RELAÇÕES
-- =====================================================

-- 3.1 Junção Importações, País e Mês para heatmap temporal
SELECT 
    p.NOME_PAIS,
    m.NOME_MES,
    SUM(i.VL_FOB) as valor_total
FROM Importacoes i
JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
JOIN Mes m ON i.COD_MES = m.COD_MES
WHERE p.NOME_PAIS IN ('CHINA', 'ESTADOS UNIDOS', 'ALEMANHA', 'ARGENTINA', 'COREIA DO SUL', 'INDIA', 'ITALIA', 'FRANCA', 'JAPAO', 'CHILE')
GROUP BY p.NOME_PAIS, m.NOME_MES, m.COD_MES
ORDER BY m.COD_MES;

-- 3.2 Junção Importações, NCM e Unidade para análise por produtos
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
LIMIT 20;

-- 3.3 Junção Importações, País, NCM e UF para análise de outliers
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
LIMIT 100;

-- =====================================================
-- CONSULTAS ADICIONAIS IDENTIFICADAS NO CÓDIGO
-- =====================================================

-- Consulta dinâmica para heatmap países/mês (template)
-- Esta consulta é construída dinamicamente no código Python
-- Exemplo de execução:
/*
SELECT 
    p.NOME_PAIS,
    m.NOME_MES,
    SUM(i.VL_FOB) as valor_total
FROM Importacoes i
JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
JOIN Mes m ON i.COD_MES = m.COD_MES
WHERE p.NOME_PAIS IN ('País1', 'País2', ..., 'PaísN')
GROUP BY p.NOME_PAIS, m.NOME_MES, m.COD_MES
ORDER BY m.COD_MES;
*/

-- =====================================================
-- RESUMO DAS CONSULTAS POR CATEGORIA
-- =====================================================

/*
TOTAL DE CONSULTAS IDENTIFICADAS: 13 consultas principais

GRUPO 1 - SELEÇÃO E PROJEÇÃO (7 consultas):
- Meses distintos
- UFs distintas  
- Total de importações
- Valor total FOB
- Países únicos
- NCMs únicos
- Análise de correlações

GRUPO 2 - JUNÇÃO DE DUAS RELAÇÕES (4 consultas):
- Importações x Mês (análise temporal)
- Importações x País (análise por países)
- Importações x UF (análise por estados)
- Top países por valor (para filtros)

GRUPO 3 - JUNÇÃO DE TRÊS OU MAIS RELAÇÕES (3 consultas):
- Importações x País x Mês (heatmap temporal)
- Importações x NCM x Unidade (análise por produtos)
- Importações x País x NCM x UF (análise de outliers)

CONSULTAS DINÂMICAS (1 template):
- Heatmap países/mês com filtros dinâmicos

OBSERVAÇÕES:
- Todas as consultas utilizam funções de agregação (COUNT, SUM, AVG)
- As junções são do tipo INNER JOIN
- Uso extensivo de GROUP BY para agregações
- Ordenação por campos relevantes (ORDER BY)
- Limitação de resultados com LIMIT em consultas de ranking
- Filtros com WHERE para análises específicas
*/
