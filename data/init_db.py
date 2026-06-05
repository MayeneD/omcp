"""
Inicializa o banco SQLite com dados de exemplo.
Executado automaticamente pelo server.py na primeira vez.
"""
import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "omcp.db"


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def init(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ── USUÁRIOS ─────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id       TEXT PRIMARY KEY,
        nome     TEXT NOT NULL,
        email    TEXT NOT NULL UNIQUE,
        perfil   TEXT NOT NULL,
        missao   TEXT NOT NULL,
        status   TEXT NOT NULL DEFAULT 'Ativo',
        senha    TEXT NOT NULL
    )""")

    usuarios = [
        ("USR-001", "Carlos Silva",  "c.silva@omcp.gov",    "Admin",      "LUNA-7", "Ativo",  hash_senha("admin123")),
        ("USR-002", "Ana Ferreira",  "a.ferreira@omcp.gov", "Operador",   "LUNA-7", "Ativo",  hash_senha("op123")),
        ("USR-003", "Pedro Mendes",  "p.mendes@omcp.gov",   "Engenheiro", "LUNA-7", "Ativo",  hash_senha("eng123")),
        ("USR-004", "Julia Costa",   "j.costa@omcp.gov",    "Analista",   "MARS-3", "Inativo",hash_senha("ana123")),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?,?,?,?)", usuarios
    )

    # ── SENSORES ──────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS sensores (
        id          TEXT PRIMARY KEY,
        nome        TEXT NOT NULL,
        tipo        TEXT NOT NULL,
        leitura     REAL NOT NULL,
        unidade     TEXT NOT NULL,
        limiar_min  REAL,
        limiar_max  REAL,
        status      TEXT NOT NULL DEFAULT 'OK',
        missao      TEXT NOT NULL DEFAULT 'LUNA-7'
    )""")

    sensores = [
        ("PROP-CAM-001",  "Câmara Propulsão",  "Pressão",     11.2,  "PSI",   15.0,  120.0, "Crítico", "LUNA-7"),
        ("ENERGY-BATT-01","Bateria Principal",  "Carga",       87.3,  "%",     20.0,  100.0, "OK",      "LUNA-7"),
        ("REACT-TEMP-003","Reator Fusão",       "Temperatura", 2847.0,"°C",    800.0, 2600.0,"Crítico", "LUNA-7"),
        ("RAD-HULL-007",  "Radiação Casco",     "Radiação",    512.0, "mSv/h", 0.0,   450.0, "Alto",    "LUNA-7"),
        ("NAV-GYRO-002",  "Giroscópio Nav.",    "Orientação",  0.003, "°/s",  -0.01,  0.01,  "OK",      "LUNA-7"),
        ("COMM-ANT-02",   "Antena Comunicação", "Sinal",       4.2,   "dB",    8.0,   30.0,  "Alto",    "LUNA-7"),
        ("FUEL-HE3-001",  "Reservatório He-3",  "Nível",       38.0,  "%",     40.0,  100.0, "Médio",   "LUNA-7"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO sensores VALUES (?,?,?,?,?,?,?,?,?)", sensores
    )

    # ── ALERTAS ───────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id           TEXT PRIMARY KEY,
        sensor_id    TEXT NOT NULL,
        titulo       TEXT NOT NULL,
        severidade   TEXT NOT NULL,
        valor        TEXT NOT NULL,
        limiar       TEXT NOT NULL,
        timestamp    TEXT NOT NULL,
        status       TEXT NOT NULL DEFAULT 'Ativo',
        confirmado_por TEXT,
        FOREIGN KEY (sensor_id) REFERENCES sensores(id)
    )""")

    alertas = [
        ("ALT-001","PROP-CAM-001", "Pressão da câmara de propulsão abaixo do mínimo crítico",
         "Crítico","11.2 PSI","15 PSI","09/06/2026 07:43:21","Ativo",None),
        ("ALT-002","REACT-TEMP-003","Temperatura do reator de fusão excedeu limite máximo",
         "Crítico","2847°C","2600°C","09/06/2026 08:11:05","Ativo",None),
        ("ALT-003","RAD-HULL-007","Taxa de radiação no casco ultrapassou nível de segurança",
         "Alto","512 mSv/h","450 mSv/h","09/06/2026 08:15:33","Ativo",None),
        ("ALT-004","COMM-ANT-02","Sinal de comunicação com base terrestre degradado",
         "Alto","4.2 dB","8 dB","09/06/2026 08:22:17","Ativo",None),
        ("ALT-005","FUEL-HE3-001","Reservatório de hélio-3 abaixo de 40% de capacidade",
         "Médio","38%","40%","09/06/2026 08:30:00","Ativo",None),
        ("ALT-006","NAV-GYRO-002","Ciclo de autoteste do giroscópio 2 concluído com aviso",
         "Baixo","0.003°","0.001°","09/06/2026 08:35:11","Ativo",None),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO alertas VALUES (?,?,?,?,?,?,?,?,?)", alertas
    )

    # ── LOG DE AUDITORIA ──────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        usuario   TEXT NOT NULL,
        acao      TEXT NOT NULL
    )""")

    logs = [
        ("09/06/2026 09:01:44","a.ferreira","Confirmou alerta PROP-CAM-001 (Crítico) — escalado para diretor"),
        ("09/06/2026 08:50:22","p.mendes",  "Atualizou limiar sensor REACT-TEMP-003: max 2600°C → 2800°C"),
        ("09/06/2026 08:43:10","c.silva",   "Cadastrou novo usuário USR-005 com perfil Operador"),
        ("09/06/2026 08:30:05","SISTEMA-IA","Alerta automático gerado: RAD-HULL-007 ultrapassou 450 mSv/h"),
        ("09/06/2026 08:11:05","SISTEMA-IA","Alerta Crítico gerado: REACT-TEMP-003 = 2847°C (limiar: 2600°C)"),
        ("09/06/2026 07:43:21","SISTEMA-IA","Alerta Crítico gerado: PROP-CAM-001 = 11.2 PSI (limiar: 15 PSI)"),
        ("09/06/2026 07:00:00","a.ferreira","Login autenticado — sessão iniciada (IP: 192.168.1.42)"),
        ("09/06/2026 06:58:33","p.mendes",  "Gerou relatório de análise preditiva (PDF, período 7d)"),
        ("09/06/2026 06:30:00","c.silva",   "Executou análise preditiva manual — missão LUNA-7"),
        ("08/06/2026 22:00:00","SISTEMA",   "Backup automático de dados concluído — 4.8GB armazenados"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO auditoria (timestamp, usuario, acao) VALUES (?,?,?)", logs
    )

    # ── CONFIGURAÇÕES ─────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    )""")

    configs = [
        ("nome_plataforma",   "Orbital Mission Control Platform"),
        ("intervalo_polling", "500"),
        ("retencao_logs",     "2 anos (padrão)"),
        ("protocolo_seg",     "TLS 1.3 (recomendado)"),
        ("missao_ativa",      "LUNA-7"),
        ("usuario_logado",    "op.silva"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO configuracoes VALUES (?,?)", configs
    )

    # ── RELATÓRIOS GERADOS ────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS relatorios (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT NOT NULL,
        tipo      TEXT NOT NULL,
        periodo   TEXT NOT NULL,
        formato   TEXT NOT NULL,
        arquivo   TEXT NOT NULL
    )""")

    relatorios = [
        ("09/06/2026 08:00","Preditiva","7 dias","PDF","relatorio_preditiva_20260609.pdf"),
        ("08/06/2026 20:00","Alertas",  "24h",   "PDF","relatorio_alertas_20260608.pdf"),
        ("07/06/2026 12:00","Status",   "1 mês", "CSV","relatorio_status_20260607.csv"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO relatorios (data_hora,tipo,periodo,formato,arquivo) VALUES (?,?,?,?,?)",
        relatorios
    )

    conn.commit()
    conn.close()
    print("  ✓ Banco de dados inicializado.")


if __name__ == "__main__":
    init()
    # Inicializa bancos alternativos se existirem mas estiverem incompletos
    for nome in ["mars3.db", "iss_emergencia.db"]:
        p = DB_PATH.parent / nome
        if p.exists():
            print(f"  ✓ {nome} já existe, mantendo dados.")
