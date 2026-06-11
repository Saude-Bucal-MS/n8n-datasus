-- Tabelas originais
CREATE TABLE IF NOT EXISTS log_processamento_arquivos (
    nome_arquivo VARCHAR(255) PRIMARY KEY,
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS populacao_municipios (
    ano VARCHAR(4),
    municipio VARCHAR(10),
    populacao_total INT DEFAULT 0,
    populacao_6_12 INT DEFAULT 0,
    PRIMARY KEY (ano, municipio)
);

CREATE TABLE IF NOT EXISTS producao_odonto_consolidada (
    data DATE,
    municipio VARCHAR(10),
    ind01_num_prim_consulta INT DEFAULT 0,
    ind02_num_trat_concluido INT DEFAULT 0,
    ind02_den_prim_consulta INT DEFAULT 0,
    ind03_num_exodontias INT DEFAULT 0,
    ind03_den_total_clinicos INT DEFAULT 0,
    ind04_num_escovacao_6_12 INT DEFAULT 0,
    ind05_num_preventivos INT DEFAULT 0,
    ind05_den_total_individuais INT DEFAULT 0,
    ind06_num_tra_art INT DEFAULT 0,
    ind06_den_restauradores INT DEFAULT 0,
    PRIMARY KEY (data, municipio)
);

-- Tabela de referência de municípios
CREATE TABLE IF NOT EXISTS municipios_ms (
    codigo_ibge INT NOT NULL,
    nome_municipio VARCHAR(100) DEFAULT NULL,
    macro_regiao VARCHAR(50) DEFAULT NULL,
    micro_regiao VARCHAR(50) DEFAULT NULL,
    PRIMARY KEY (codigo_ibge)
);

-- Popula municipios_ms com dados de Mato Grosso do Sul (apenas se estiver vazio)
INSERT IGNORE INTO municipios_ms (codigo_ibge, nome_municipio, macro_regiao, micro_regiao) VALUES 
(500020,'Água Clara','COSTA LESTE','LESTE'),
(500025,'Alcinópolis','CENTRO','NORTE'),
(500060,'Amambai','SUL','SUL FRONTEIRA'),
(500070,'Anastácio','CENTRO','BAIXO PANTANAL'),
(500080,'Anaurilândia','SUL','SUDESTE'),
(500085,'Angélica','SUL','SUDESTE'),
(500090,'Antônio João','SUL','SUL FRONTEIRA'),
(500100,'Aparecida do Taboado','COSTA LESTE','NORDESTE'),
(500110,'Aquidauana','CENTRO','BAIXO PANTANAL'),
(500124,'Aral Moreira','SUL','SUL FRONTEIRA'),
(500150,'Bandeirantes','CENTRO','CENTRO'),
(500190,'Bataguassu','COSTA LESTE','LESTE'),
(500200,'Batayporã','SUL','SUDESTE'),
(500210,'Bela Vista','CENTRO','BAIXO PANTANAL'),
(500215,'Bodoquena','CENTRO','BAIXO PANTANAL'),
(500220,'Bonito','CENTRO','BAIXO PANTANAL'),
(500230,'Brasilândia','COSTA LESTE','LESTE'),
(500240,'Caarapó','SUL','CENTRO SUL'),
(500260,'Camapuã','CENTRO','CENTRO'),
(500270,'Campo Grande','CENTRO','CENTRO'),
(500280,'Caracol','CENTRO','BAIXO PANTANAL'),
(500290,'Cassilândia','COSTA LESTE','NORDESTE'),
(500295,'Chapadão do Sul','COSTA LESTE','NORDESTE'),
(500310,'Corguinho','CENTRO','CENTRO'),
(500315,'Coronel Sapucaia','SUL','SUL FRONTEIRA'),
(500320,'Corumbá','PANTANAL','PANTANAL'),
(500325,'Costa Rica','COSTA LESTE','NORDESTE'),
(500330,'Coxim','CENTRO','NORTE'),
(500345,'Deodápolis','SUL','CENTRO SUL'),
(500348,'Dois Irmãos do Buriti','CENTRO','BAIXO PANTANAL'),
(500350,'Douradina','SUL','CENTRO SUL'),
(500370,'Dourados','SUL','CENTRO SUL'),
(500375,'Eldorado','SUL','SUL FRONTEIRA'),
(500380,'Fátima do Sul','SUL','CENTRO SUL'),
(500390,'Figueirão','CENTRO','NORTE'),
(500400,'Glória de Dourados','SUL','CENTRO SUL'),
(500410,'Guia Lopes da Laguna','CENTRO','BAIXO PANTANAL'),
(500430,'Iguatemi','SUL','SUL FRONTEIRA'),
(500440,'Inocência','COSTA LESTE','NORDESTE'),
(500450,'Itaporã','SUL','CENTRO SUL'),
(500460,'Itaquiraí','SUL','SUL FRONTEIRA'),
(500470,'Ivinhema','SUL','SUDESTE'),
(500480,'Japorã','SUL','SUL FRONTEIRA'),
(500490,'Jaraguari','CENTRO','CENTRO'),
(500500,'Jardim','CENTRO','BAIXO PANTANAL'),
(500510,'Jateí','SUL','CENTRO SUL'),
(500515,'Juti','SUL','SUL FRONTEIRA'),
(500520,'Ladário','PANTANAL','PANTANAL'),
(500525,'Laguna Carapã','SUL','CENTRO SUL'),
(500540,'Maracaju','CENTRO','BAIXO PANTANAL'),
(500560,'Miranda','PANTANAL','PANTANAL'),
(500568,'Mundo Novo','SUL','SUL FRONTEIRA'),
(500570,'Naviraí','SUL','SUL FRONTEIRA'),
(500580,'Nioaque','CENTRO','BAIXO PANTANAL'),
(500600,'Nova Alvorada do Sul','SUL','CENTRO SUL'),
(500620,'Nova Andradina','SUL','SUDESTE'),
(500625,'Novo Horizonte do Sul','SUL','SUDESTE'),
(500627,'Paraíso das Águas','COSTA LESTE','NORDESTE'),
(500630,'Paranaíba','COSTA LESTE','NORDESTE'),
(500635,'Paranhos','SUL','SUL FRONTEIRA'),
(500640,'Pedro Gomes','CENTRO','NORTE'),
(500660,'Ponta Porã','SUL','SUL FRONTEIRA'),
(500690,'Porto Murtinho','CENTRO','BAIXO PANTANAL'),
(500710,'Ribas do Rio Pardo','CENTRO','CENTRO'),
(500720,'Rio Brilhante','SUL','CENTRO SUL'),
(500730,'Rio Negro','CENTRO','NORTE'),
(500740,'Rio Verde de Mato Grosso','CENTRO','NORTE'),
(500750,'Rochedo','CENTRO','CENTRO'),
(500755,'Santa Rita do Pardo','COSTA LESTE','LESTE'),
(500769,'São Gabriel do Oeste','CENTRO','NORTE'),
(500770,'Sete Quedas','SUL','SUL FRONTEIRA'),
(500780,'Selvíria','COSTA LESTE','LESTE'),
(500790,'Sidrolândia','CENTRO','CENTRO'),
(500793,'Sonora','CENTRO','NORTE'),
(500795,'Tacuru','SUL','SUL FRONTEIRA'),
(500797,'Taquarussu','SUL','SUDESTE'),
(500800,'Terenos','CENTRO','CENTRO'),
(500830,'Três Lagoas','COSTA LESTE','LESTE'),
(500840,'Vicentina','SUL','CENTRO SUL');

-- View de população com nome do município (join direto com municipios_ms)
CREATE OR REPLACE VIEW v_populacao_municipios AS
SELECT 
    pom.municipio,
    COALESCE(mm.nome_municipio, pom.municipio) AS nome_municipio,
    pom.ano,
    '01' AS mes,
    pom.populacao_total,
    pom.populacao_6_12
FROM populacao_municipios pom
LEFT JOIN municipios_ms mm ON LPAD(mm.codigo_ibge, 6, '0') = pom.municipio;

-- View de produção com nome do município (join direto com municipios_ms)
CREATE OR REPLACE VIEW v_producao_odonto_consolidada AS
SELECT 
    poc.municipio,
    COALESCE(mm.nome_municipio, poc.municipio) AS nome_municipio,
    YEAR(poc.data) AS ano,
    MONTH(poc.data) AS mes,
    poc.ind01_num_prim_consulta,
    poc.ind02_num_trat_concluido,
    poc.ind02_den_prim_consulta,
    poc.ind03_num_exodontias,
    poc.ind03_den_total_clinicos,
    poc.ind04_num_escovacao_6_12,
    poc.ind05_num_preventivos,
    poc.ind05_den_total_individuais,
    poc.ind06_num_tra_art,
    poc.ind06_den_restauradores
FROM producao_odonto_consolidada poc
LEFT JOIN municipios_ms mm ON LPAD(mm.codigo_ibge, 6, '0') = poc.municipio;

-- View consolidada (população + produção com nomes)
CREATE OR REPLACE VIEW v_consolidada AS
SELECT 
    COALESCE(p.municipio, prod.municipio) AS municipio,
    COALESCE(p.nome_municipio, prod.nome_municipio) AS nome_municipio,
    COALESCE(p.ano, prod.ano) AS ano,
    COALESCE(p.mes, prod.mes) AS mes,
    p.populacao_total,
    p.populacao_6_12,
    prod.ind01_num_prim_consulta,
    prod.ind02_num_trat_concluido,
    prod.ind02_den_prim_consulta,
    prod.ind03_num_exodontias,
    prod.ind03_den_total_clinicos,
    prod.ind04_num_escovacao_6_12,
    prod.ind05_num_preventivos,
    prod.ind05_den_total_individuais,
    prod.ind06_num_tra_art,
    prod.ind06_den_restauradores
FROM v_populacao_municipios p
FULL OUTER JOIN v_producao_odonto_consolidada prod 
    ON p.municipio = prod.municipio 
    AND p.ano = prod.ano 
    AND p.mes = prod.mes;
