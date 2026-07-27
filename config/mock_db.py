# mock_db.py — banco SQLite local que imita o Oracle para o TCC funcionar sem conexão
import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mock.db')


def _get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS login_user_data (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            email     TEXT NOT NULL UNIQUE,
            login_password TEXT NOT NULL,
            num_oab   TEXT,
            username  TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            data_creiacao TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS estados_brasil (
            nome_estado  TEXT NOT NULL,
            sigla_estado TEXT NOT NULL,
            PRIMARY KEY (sigla_estado)
        );

        CREATE TABLE IF NOT EXISTS classes_processo (
            classe_processo TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS caminho_processo (
            caminho_processual TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS processos_juridicos (
            numero_processo        TEXT PRIMARY KEY,
            classe_processo        TEXT,
            rito_processo          TEXT,
            nome_advogado          TEXT,
            numero_oab             TEXT,
            nome_cliente_empresa   TEXT,
            caminho_processual     TEXT,
            nome_juiz              TEXT,
            estado_processo        TEXT,
            valor_causa            REAL,
            valor_deferido_causa   REAL,
            valor_pago_causa       REAL,
            observacoes_clob       TEXT,
            justica                TEXT,
            tribunal               TEXT,
            data_cadastro          TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS arquivos_processos (
            id_arquivo      INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT,
            nome_arquivo    TEXT,
            arquivo_pdf     BLOB,
            FOREIGN KEY (numero_processo) REFERENCES processos_juridicos(numero_processo) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS datajud_endpoints (
            justica  TEXT NOT NULL,
            tribunal TEXT NOT NULL,
            endpoint TEXT NOT NULL
        );
    """)

    # Seed: usuário admin
    cur.execute("INSERT OR IGNORE INTO login_user_data(name, email, login_password, num_oab, username) VALUES (?,?,?,?,?)",
                ('admin', 'admin@gmail.com', '1234', '0099887766', 'admin'))
    cur.execute("INSERT OR IGNORE INTO users(username, password) VALUES (?,?)", ('admin', 'admin'))

    # Seed: estados
    estados = [
        ('Acre','AC'),('Alagoas','AL'),('Amapá','AP'),('Amazonas','AM'),('Bahia','BA'),
        ('Ceará','CE'),('Distrito Federal','DF'),('Espírito Santo','ES'),('Goiás','GO'),
        ('Maranhão','MA'),('Mato Grosso','MT'),('Mato Grosso do Sul','MS'),('Minas Gerais','MG'),
        ('Pará','PA'),('Paraíba','PB'),('Paraná','PR'),('Pernambuco','PE'),('Piauí','PI'),
        ('Rio de Janeiro','RJ'),('Rio Grande do Norte','RN'),('Rio Grande do Sul','RS'),
        ('Rondônia','RO'),('Roraima','RR'),('Santa Catarina','SC'),('São Paulo','SP'),
        ('Sergipe','SE'),('Tocantins','TO'),
    ]
    cur.executemany("INSERT OR IGNORE INTO estados_brasil(nome_estado, sigla_estado) VALUES (?,?)", estados)

    # Seed: classes de processo
    classes = [
        ('Ação Trabalhista',),('Ação Civil',),('Ação Penal',),('Ação Tributária',),
        ('Ação Administrativa',),('Ação Empresarial',),('Ação Constitucional',),
    ]
    cur.executemany("INSERT OR IGNORE INTO classes_processo(classe_processo) VALUES (?)", classes)

    # Seed: caminho processual
    caminhos = [
        ('Petição Inicial',),('Intimação',),('Contestação',),('Notificação',),
        ('Conciliação',),('Sentença',),('Apelação',),
    ]
    cur.executemany("INSERT OR IGNORE INTO caminho_processo(caminho_processual) VALUES (?)", caminhos)

    # Seed: endpoints DataJud (tribunais principais)
    endpoints = [
        ('Tribunais Superiores','Tribunal Superior do Trabalho','https://api-publica.datajud.cnj.jus.br/api_publica_tst/_search'),
        ('Tribunais Superiores','Tribunal Superior Eleitoral','https://api-publica.datajud.cnj.jus.br/api_publica_tse/_search'),
        ('Tribunais Superiores','Tribunal Superior de Justiça','https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search'),
        ('Tribunais Superiores','Tribunal Superior Militar','https://api-publica.datajud.cnj.jus.br/api_publica_stm/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 1ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf1/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 2ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf2/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 3ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf3/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 4ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf4/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 5ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf5/_search'),
        ('Justiça Federal','Tribunal Regional Federal da 6ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trf6/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Acre','https://api-publica.datajud.cnj.jus.br/api_publica_tjac/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Alagoas','https://api-publica.datajud.cnj.jus.br/api_publica_tjal/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Amazonas','https://api-publica.datajud.cnj.jus.br/api_publica_tjam/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Amapá','https://api-publica.datajud.cnj.jus.br/api_publica_tjap/_search'),
        ('Justiça Estadual','Tribunal de Justiça da Bahia','https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Ceará','https://api-publica.datajud.cnj.jus.br/api_publica_tjce/_search'),
        ('Justiça Estadual','TJ do Distrito Federal e Territórios','https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Espírito Santo','https://api-publica.datajud.cnj.jus.br/api_publica_tjes/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Goiás','https://api-publica.datajud.cnj.jus.br/api_publica_tjgo/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Maranhão','https://api-publica.datajud.cnj.jus.br/api_publica_tjma/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Minas Gerais','https://api-publica.datajud.cnj.jus.br/api_publica_tjmg/_search'),
        ('Justiça Estadual','TJ do Mato Grosso de Sul','https://api-publica.datajud.cnj.jus.br/api_publica_tjms/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Mato Grosso','https://api-publica.datajud.cnj.jus.br/api_publica_tjmt/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Pará','https://api-publica.datajud.cnj.jus.br/api_publica_tjpa/_search'),
        ('Justiça Estadual','Tribunal de Justiça da Paraíba','https://api-publica.datajud.cnj.jus.br/api_publica_tjpb/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Pernambuco','https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Piauí','https://api-publica.datajud.cnj.jus.br/api_publica_tjpi/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Paraná','https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Rio de Janeiro','https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search'),
        ('Justiça Estadual','TJ do Rio Grande do Norte','https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Rondônia','https://api-publica.datajud.cnj.jus.br/api_publica_tjro/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Roraima','https://api-publica.datajud.cnj.jus.br/api_publica_tjrr/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Rio Grande do Sul','https://api-publica.datajud.cnj.jus.br/api_publica_tjrs/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Santa Catarina','https://api-publica.datajud.cnj.jus.br/api_publica_tjsc/_search'),
        ('Justiça Estadual','Tribunal de Justiça de Sergipe','https://api-publica.datajud.cnj.jus.br/api_publica_tjse/_search'),
        ('Justiça Estadual','Tribunal de Justiça de São Paulo','https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search'),
        ('Justiça Estadual','Tribunal de Justiça do Tocantins','https://api-publica.datajud.cnj.jus.br/api_publica_tjto/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 1ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt1/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 2ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt2/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 3ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt3/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 4ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt4/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 5ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt5/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 6ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt6/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 7ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt7/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 8ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt8/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 9ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt9/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 10ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt10/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 11ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt11/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 12ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt12/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 13ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt13/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 14ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt14/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 15ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt15/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 16ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt16/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 17ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt17/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 18ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt18/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 19ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt19/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 20ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt20/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 21ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt21/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 22ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt22/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 23ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt23/_search'),
        ('Justiça do Trabalho','Tribunal Regional do Trabalho da 24ª Região','https://api-publica.datajud.cnj.jus.br/api_publica_trt24/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Acre','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ac/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Alagoas','https://api-publica.datajud.cnj.jus.br/api_publica_tre-al/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Amazonas','https://api-publica.datajud.cnj.jus.br/api_publica_tre-am/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Amapá','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ap/_search'),
        ('Justiça Eleitoral','Tribunal de Justiça da Bahia','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ba/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Ceará','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ce/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Distrito Federal','https://api-publica.datajud.cnj.jus.br/api_publica_tre-dft/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Espírito Santo','https://api-publica.datajud.cnj.jus.br/api_publica_tre-es/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Goiás','https://api-publica.datajud.cnj.jus.br/api_publica_tre-go/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Maranhão','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ma/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Minas Gerais','https://api-publica.datajud.cnj.jus.br/api_publica_tre-mg/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Mato Grosso de Sul','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ms/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Mato Grosso','https://api-publica.datajud.cnj.jus.br/api_publica_tre-mt/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Pará','https://api-publica.datajud.cnj.jus.br/api_publica_tre-pa/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral da Paraíba','https://api-publica.datajud.cnj.jus.br/api_publica_tre-pb/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Pernambuco','https://api-publica.datajud.cnj.jus.br/api_publica_tre-pe/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Piauí','https://api-publica.datajud.cnj.jus.br/api_publica_tre-pi/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Paraná','https://api-publica.datajud.cnj.jus.br/api_publica_tre-pr/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Rio de Janeiro','https://api-publica.datajud.cnj.jus.br/api_publica_tre-rj/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Rio Grande do Norte','https://api-publica.datajud.cnj.jus.br/api_publica_tre-rn/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Rondônia','https://api-publica.datajud.cnj.jus.br/api_publica_tre-ro/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Roraima','https://api-publica.datajud.cnj.jus.br/api_publica_tre-rr/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Rio Grande do Sul','https://api-publica.datajud.cnj.jus.br/api_publica_tre-rs/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Santa Catarina','https://api-publica.datajud.cnj.jus.br/api_publica_tre-sc/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de Sergipe','https://api-publica.datajud.cnj.jus.br/api_publica_tre-se/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral de São Paulo','https://api-publica.datajud.cnj.jus.br/api_publica_tre-sp/_search'),
        ('Justiça Eleitoral','Tribunal Regional Eleitoral do Tocantins','https://api-publica.datajud.cnj.jus.br/api_publica_tre-to/_search'),
        ('Justiça Militar','Tribunal Justiça Militar de Minas Gerais','https://api-publica.datajud.cnj.jus.br/api_publica_tjmmg/_search'),
        ('Justiça Militar','Tribunal Justiça Militar do Rio Grande do Sul','https://api-publica.datajud.cnj.jus.br/api_publica_tjmrs/_search'),
        ('Justiça Militar','Tribunal Justiça Militar de São Paulo','https://api-publica.datajud.cnj.jus.br/api_publica_tjmsp/_search'),
    ]
    cur.executemany("INSERT OR IGNORE INTO datajud_endpoints(justica, tribunal, endpoint) VALUES (?,?,?)", endpoints)

    # Seed: processos fictícios de amostragem para o admin
    # formato: (numero, classe, rito, advogado, oab, cliente, caminho, juiz, estado,
    #           valor_causa, valor_deferido, valor_pago, obs, justica, tribunal, data_cadastro)
    processos_exemplo = [
        ('0004521-11.2022.5.03.0137', 'Ação Trabalhista', 'Ordinário', 'Maria Silva', '12345/SP',
         'Transportadora Rápida Ltda', 'Sentença', 'Dra. Camila Rocha', 'MG',
         45000.00, 38000.00, 38000.00,
         'Reconhecimento de vínculo empregatício e pagamento de horas extras. Sentença favorável ao reclamante.',
         'Justiça do Trabalho', 'Tribunal Regional do Trabalho da 3ª Região', '2025-08-10'),

        ('5009871-12.2023.4.04.7100', 'Ação Tributária', 'Ordinário', 'Maria Silva', '12345/SP',
         'Comércio e Exportação Sul Ltda', 'Apelação', 'Dra. Renata Borges', 'RS',
         180000.00, 150000.00, 75000.00,
         'Ação anulatória de auto de infração fiscal referente a contribuições previdenciárias.',
         'Justiça Federal', 'Tribunal Regional Federal da 4ª Região', '2025-09-05'),

        ('0009876-54.2022.8.26.0100', 'Ação Civil', 'Ordinário', 'Maria Silva', '12345/SP',
         'Construtora ABC Ltda', 'Apelação', 'Dra. Ana Costa', 'SP',
         120000.00, 95000.00, 47500.00,
         'Ação de indenização por danos materiais e morais decorrentes de vícios na construção do imóvel.',
         'Justiça Estadual', 'Tribunal de Justiça de São Paulo', '2025-09-22'),

        ('5001122-33.2024.4.03.6100', 'Ação Tributária', 'Ordinário', 'Maria Silva', '12345/SP',
         'Indústria Metalúrgica XYZ S.A.', 'Sentença', 'Dr. Carlos Mendes', 'SP',
         350000.00, 280000.00, 140000.00,
         'Mandado de segurança para suspensão de exigibilidade de crédito tributário de ICMS. Sentença procedente.',
         'Justiça Federal', 'Tribunal Regional Federal da 3ª Região', '2025-10-14'),

        ('0001234-56.2023.5.02.0001', 'Ação Trabalhista', 'Sumaríssimo', 'Maria Silva', '12345/SP',
         'João da Silva ME', 'Contestação', 'Dr. Roberto Alves', 'SP',
         15000.00, 12000.00, 6000.00,
         'Reclamação trabalhista por verbas rescisórias não pagas: FGTS, férias e 13º salário.',
         'Justiça do Trabalho', 'Tribunal Regional do Trabalho da 2ª Região', '2025-10-28'),

        ('0023456-91.2022.8.13.0024', 'Ação Empresarial', 'Ordinário', 'Maria Silva', '12345/SP',
         'Tech Solutions Desenvolvimento de Software Ltda', 'Conciliação', 'Dra. Juliana Martins', 'MG',
         200000.00, 0.00, 0.00,
         'Ação de dissolução parcial de sociedade com apuração de haveres. Em fase de conciliação.',
         'Justiça Estadual', 'Tribunal de Justiça de Minas Gerais', '2025-11-08'),

        ('0003317-88.2023.8.19.0001', 'Ação Civil', 'Sumário', 'Maria Silva', '12345/SP',
         'Banco Seguro S.A.', 'Intimação', 'Dr. Marcos Ferreira', 'RJ',
         65000.00, 0.00, 0.00,
         'Ação revisional de contrato bancário com cobrança de juros abusivos e danos morais por negativação indevida.',
         'Justiça Estadual', 'Tribunal de Justiça do Rio de Janeiro', '2025-11-19'),

        ('1005432-77.2023.4.01.3400', 'Ação Administrativa', 'Ordinário', 'Maria Silva', '12345/SP',
         'Instituto Federal de Brasília', 'Notificação', 'Dr. Antônio Souza', 'DF',
         80000.00, 0.00, 0.00,
         'Mandado de segurança contra ato administrativo de exoneração de servidor público estável.',
         'Justiça Federal', 'Tribunal Regional Federal da 1ª Região', '2025-12-03'),

        ('0007843-29.2024.5.15.0001', 'Ação Trabalhista', 'Sumaríssimo', 'Maria Silva', '12345/SP',
         'Supermercado Bom Preço S.A.', 'Conciliação', 'Dr. Paulo Henrique Lima', 'SP',
         32000.00, 0.00, 0.00,
         'Pedido de pagamento de horas extras e adicional noturno. Em fase de conciliação.',
         'Justiça do Trabalho', 'Tribunal Regional do Trabalho da 15ª Região', '2025-12-17'),

        ('0011982-44.2024.8.16.0001', 'Ação Civil', 'Ordinário', 'Maria Silva', '12345/SP',
         'Plano de Saúde VidaBoa Ltda', 'Petição Inicial', 'Dra. Fernanda Oliveira', 'PR',
         95000.00, 0.00, 0.00,
         'Ação de obrigação de fazer c/c indenização por recusa de cobertura de procedimento cirúrgico.',
         'Justiça Estadual', 'Tribunal de Justiça do Paraná', '2026-01-09'),

        ('0001593-45.2023.8.19.0014', 'Ação Penal', 'Ordinário', 'Maria Silva', '12345/SP',
         'Ministério Público do RJ (réu: Carlos Alberto Nunes)', 'Contestação', 'Dr. Eduardo Pinto', 'RJ',
         0.00, 0.00, 0.00,
         'Defesa em ação penal por crime de estelionato qualificado. Réu responde em liberdade.',
         'Justiça Estadual', 'Tribunal de Justiça do Rio de Janeiro', '2026-02-14'),

        ('0088712-05.2024.3.00.0000', 'Ação Constitucional', 'Ordinário', 'Maria Silva', '12345/SP',
         'Associação dos Servidores Municipais de SP', 'Petição Inicial', 'Min. Dra. Beatriz Andrade', 'SP',
         0.00, 0.00, 0.00,
         'Mandado de injunção coletivo para regulamentação do direito de greve dos servidores públicos municipais.',
         'Tribunais Superiores', 'Tribunal Superior de Justiça', '2026-03-20'),
    ]
    for p in processos_exemplo:
        cur.execute("""
            INSERT OR IGNORE INTO processos_juridicos
            (numero_processo, classe_processo, rito_processo, nome_advogado, numero_oab,
             nome_cliente_empresa, caminho_processual, nome_juiz, estado_processo,
             valor_causa, valor_deferido_causa, valor_pago_causa, observacoes_clob,
             justica, tribunal, data_cadastro)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, p)

    conn.commit()
    conn.close()


# --- Cursor adaptador que imita cx_Oracle para o código existente ---

class MockCursor:
    def __init__(self, sqlite_conn):
        self._conn = sqlite_conn
        self._cur = sqlite_conn.cursor()
        self.description = None
        self._rows = []

    def execute(self, sql, params=None):
        # Converte bind variables Oracle (:nome / :1) para SQLite (?)
        import re
        sql_lite = re.sub(r':\w+', '?', sql)
        if params is None:
            self._cur.execute(sql_lite)
        elif isinstance(params, dict):
            positional = list(params.values())
            self._cur.execute(sql_lite, positional)
        else:
            self._cur.execute(sql_lite, params)
        self.description = self._cur.description
        self._rows = self._cur.fetchall() if self._cur.description else []
        return self

    def fetchall(self):
        return [tuple(r) for r in self._rows]

    def setinputsizes(self, **kwargs):
        pass  # sem efeito no SQLite

    def callproc(self, name, params=None):
        pass

    def close(self):
        pass


class MockConnection:
    def __init__(self, sqlite_conn, username=None):
        self._conn = sqlite_conn
        self.username = username

    def cursor(self):
        return MockCursor(self._conn)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def mock_database_connection(username=None):
    """Retorna (MockConnection, MockCursor) imitando cx_Oracle.connect()."""
    _init_db()
    raw = _get_connection()
    conn = MockConnection(raw, username)
    cursor = conn.cursor()
    return conn, cursor


def mock_get_data(query, cursor):
    """Executa query e retorna DataFrame com colunas em maiúsculo (igual ao Oracle)."""
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        if cursor.description is None:
            return pd.DataFrame()
        columns = [desc[0].upper() for desc in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    except Exception:
        return None


def mock_insert_process(register_process_dict, conn):
    """Substitui a stored procedure Oracle inserir_processo_com_arquivo."""
    import datetime
    cur = conn.cursor()
    d = register_process_dict
    cur.execute("""
        INSERT OR REPLACE INTO processos_juridicos
        (numero_processo, classe_processo, rito_processo, nome_advogado, numero_oab,
         nome_cliente_empresa, caminho_processual, nome_juiz, estado_processo,
         valor_causa, valor_deferido_causa, valor_pago_causa, observacoes_clob,
         justica, tribunal, data_cadastro)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        d.get('p_numero_processo'), d.get('p_classe_processo'), d.get('p_rito_processo'),
        d.get('p_nome_advogado'), d.get('p_numero_oab'), d.get('p_nome_cliente_empresa'),
        d.get('p_caminho_processual'), d.get('p_nome_juiz'), d.get('p_estado_processo'),
        d.get('p_valor_causa'), d.get('p_valor_definido_causa'), d.get('p_valor_pago_causa'),
        d.get('p_observacoes_clob'), d.get('p_justica'), d.get('p_tribunal'),
        datetime.date.today().isoformat(),
    ))
    if d.get('p_nome_arquivo'):
        cur.execute("""
            INSERT INTO arquivos_processos(numero_processo, nome_arquivo, arquivo_pdf)
            VALUES (?,?,?)
        """, (d.get('p_numero_processo'), d.get('p_nome_arquivo'), d.get('p_arquivo_pdf')))
    conn.commit()
    return True
