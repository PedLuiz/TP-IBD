-- =====================================================
-- CONSULTAS SQL DO DASHBOARD DE IMPORTAÇÕES BRASIL 2024
-- =====================================================
-- Arquivo: consultas.sql
-- Descrição: Consultas extraídas do arquivo streamlit.py
-- Organizadas conforme os requisitos:
-- • 2 consultas envolvendo seleção e projeção
-- • 3 consultas envolvendo junção de duas relações
-- • 3 consultas envolvendo junção de três ou mais relações
-- • 2 consultas envolvendo funções de agregação sobre junção de pelo menos duas relações
-- =====================================================

-- =====================================================
-- 1. CONSULTAS ENVOLVENDO SELEÇÃO E PROJEÇÃO (2)
-- =====================================================

-- 1.1 Seleção e projeção de meses distintos
SELECT DISTINCT COD_MES, NOME_MES 
FROM Mes 
ORDER BY COD_MES;

-- 1.2 Seleção e projeção de UFs distintas
SELECT DISTINCT COD_UF, NOME_UF 
FROM UF 
ORDER BY NOME_UF;

-- =====================================================
-- 2. CONSULTAS ENVOLVENDO JUNÇÃO DE DUAS RELAÇÕES (3)
-- =====================================================

-- 2.1 Junção entre Importações e Mês para análise temporal
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

-- 2.2 Junção entre Importações e País para análise por país
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

-- 2.3 Junção entre Importações e UF para análise por estados
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

-- =====================================================
-- 3. CONSULTAS ENVOLVENDO JUNÇÃO DE TRÊS OU MAIS RELAÇÕES (3)
-- =====================================================

-- 3.1 Junção entre Importações, País e Mês para heatmap temporal por país
SELECT 
    p.NOME_PAIS,
    m.NOME_MES,
    SUM(i.VL_FOB) as valor_total
FROM Importacoes i
JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
JOIN Mes m ON i.COD_MES = m.COD_MES
GROUP BY p.NOME_PAIS, m.NOME_MES, m.COD_MES
ORDER BY m.COD_MES;

-- 3.2 Junção entre Importações, NCM e Unidade para análise por produtos
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

-- 3.3 Junção entre Importações, País, NCM e UF para análise de outliers
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
-- 4. CONSULTAS COM FUNÇÕES DE AGREGAÇÃO SOBRE JUNÇÃO DE DUAS OU MAIS RELAÇÕES (2)
-- =====================================================

-- 4.1 Agregação para top países por valor total (funções: SUM, COUNT, AVG)
SELECT p.COD_PAIS, p.NOME_PAIS, SUM(i.VL_FOB) as total_value
FROM Importacoes i
JOIN Pais p ON i.COD_PAIS = p.COD_PAIS
GROUP BY p.COD_PAIS, p.NOME_PAIS
ORDER BY total_value DESC
LIMIT 20;

-- 4.2 Agregação para análise de correlações (funções de seleção com WHERE)
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
-- CONSULTAS ADICIONAIS PARA ESTATÍSTICAS BÁSICAS
-- =====================================================

-- Total de importações
SELECT COUNT(*) as total FROM Importacoes;

-- Valor total FOB
SELECT SUM(VL_FOB) as total_value FROM Importacoes;

-- Países únicos
SELECT COUNT(DISTINCT COD_PAIS) as countries FROM Importacoes;

-- NCMs únicos
SELECT COUNT(DISTINCT COD_NCM) as ncms FROM Importacoes;