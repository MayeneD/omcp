"""
Camada de acesso ao banco SQLite.
Todas as queries ficam aqui — o server.py só chama essas funções.
"""
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "omcp.db"

# Banco ativo — pode ser trocado em runtime pelo servidor
_db_ativo = DB_PATH


def set_db(path: Path):
    global _db_ativo
    _db_ativo = path


def get_db() -> Path:
    return _db_ativo


def get_conn():
    conn = sqlite3.connect(_db_ativo)
    conn.row_factory = sqlite3.Row
    return conn


def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def registrar_log(usuario: str, acao: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auditoria (timestamp, usuario, acao) VALUES (?,?,?)",
            (now(), usuario, acao)
        )


# ── AUTH ──────────────────────────────────────────────────────────────────

def autenticar(email: str, senha: str):
    h = hashlib.sha256(senha.encode()).hexdigest()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email=? AND senha=? AND status='Ativo'",
            (email, h)
        ).fetchone()
    return dict(row) if row else None


# ── USUÁRIOS ──────────────────────────────────────────────────────────────

def listar_usuarios():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def buscar_usuario(uid: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None


def criar_usuario(dados: dict, autor: str):
    h = hashlib.sha256(dados["senha"].encode()).hexdigest()
    # Gera próximo ID
    with get_conn() as conn:
        rows = conn.execute("SELECT id FROM usuarios ORDER BY id DESC LIMIT 1").fetchone()
        num = int(rows["id"].split("-")[1]) + 1 if rows else 1
        uid = f"USR-{num:03d}"
        conn.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)",
            (uid, dados["nome"], dados["email"], dados["perfil"],
             dados["missao"], dados.get("status","Ativo"), h)
        )
    registrar_log(autor, f"Criou usuário {uid} ({dados['nome']}) — perfil {dados['perfil']}")
    return uid


def atualizar_usuario(uid: str, dados: dict, autor: str):
    with get_conn() as conn:
        if dados.get("senha"):
            h = hashlib.sha256(dados["senha"].encode()).hexdigest()
            conn.execute(
                "UPDATE usuarios SET nome=?,email=?,perfil=?,missao=?,status=?,senha=? WHERE id=?",
                (dados["nome"], dados["email"], dados["perfil"],
                 dados["missao"], dados["status"], h, uid)
            )
        else:
            conn.execute(
                "UPDATE usuarios SET nome=?,email=?,perfil=?,missao=?,status=? WHERE id=?",
                (dados["nome"], dados["email"], dados["perfil"],
                 dados["missao"], dados["status"], uid)
            )
    registrar_log(autor, f"Atualizou usuário {uid} ({dados['nome']})")


def deletar_usuario(uid: str, autor: str):
    with get_conn() as conn:
        row = conn.execute("SELECT nome FROM usuarios WHERE id=?", (uid,)).fetchone()
        conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    if row:
        registrar_log(autor, f"Removeu usuário {uid} ({row['nome']})")


# ── SENSORES ──────────────────────────────────────────────────────────────

def listar_sensores():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sensores ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def buscar_sensor(sid: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sensores WHERE id=?", (sid,)).fetchone()
    return dict(row) if row else None


def criar_sensor(dados: dict, autor: str):
    # Calcula status automaticamente
    status = _calcular_status(
        float(dados["leitura"]),
        float(dados.get("limiar_min") or 0),
        float(dados.get("limiar_max") or 9999)
    )
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sensores VALUES (?,?,?,?,?,?,?,?,?)",
            (dados["id"], dados["nome"], dados["tipo"],
             float(dados["leitura"]), dados["unidade"],
             float(dados.get("limiar_min") or 0),
             float(dados.get("limiar_max") or 9999),
             status, dados.get("missao","LUNA-7"))
        )
    registrar_log(autor, f"Cadastrou sensor {dados['id']} ({dados['nome']})")
    return dados["id"]


def atualizar_sensor(sid: str, dados: dict, autor: str):
    status = _calcular_status(
        float(dados["leitura"]),
        float(dados.get("limiar_min") or 0),
        float(dados.get("limiar_max") or 9999)
    )
    with get_conn() as conn:
        conn.execute(
            """UPDATE sensores SET nome=?,tipo=?,leitura=?,unidade=?,
               limiar_min=?,limiar_max=?,status=?,missao=? WHERE id=?""",
            (dados["nome"], dados["tipo"], float(dados["leitura"]),
             dados["unidade"], float(dados.get("limiar_min") or 0),
             float(dados.get("limiar_max") or 9999),
             status, dados.get("missao","LUNA-7"), sid)
        )
    registrar_log(autor, f"Atualizou sensor {sid} — leitura={dados['leitura']} {dados['unidade']}")
    # Gera alerta se status crítico/alto
    if status in ("Crítico", "Alto"):
        _auto_alerta(sid, dados, status, autor)


def deletar_sensor(sid: str, autor: str):
    with get_conn() as conn:
        row = conn.execute("SELECT nome FROM sensores WHERE id=?", (sid,)).fetchone()
        conn.execute("DELETE FROM sensores WHERE id=?", (sid,))
    if row:
        registrar_log(autor, f"Removeu sensor {sid} ({row['nome']})")


def _calcular_status(leitura, limiar_min, limiar_max):
    if limiar_min and leitura < limiar_min:
        diff = (limiar_min - leitura) / limiar_min
        return "Crítico" if diff > 0.20 else "Alto" if diff > 0.10 else "Médio"
    if limiar_max and leitura > limiar_max:
        diff = (leitura - limiar_max) / limiar_max
        return "Crítico" if diff > 0.10 else "Alto" if diff > 0.05 else "Médio"
    return "OK"


def _auto_alerta(sid, dados, status, autor):
    with get_conn() as conn:
        existe = conn.execute(
            "SELECT id FROM alertas WHERE sensor_id=? AND status='Ativo'", (sid,)
        ).fetchone()
        if not existe:
            aid = f"ALT-AUTO-{sid}"
            conn.execute(
                "INSERT OR REPLACE INTO alertas VALUES (?,?,?,?,?,?,?,?,?)",
                (aid, sid,
                 f"Leitura fora do limiar: {dados['nome']}",
                 status,
                 f"{dados['leitura']} {dados['unidade']}",
                 f"Mín:{dados.get('limiar_min')} / Máx:{dados.get('limiar_max')}",
                 now(), "Ativo", None)
            )
    registrar_log(autor, f"Alerta automático gerado para sensor {sid} — status {status}")


# ── ALERTAS ───────────────────────────────────────────────────────────────

def listar_alertas(severidade=None):
    with get_conn() as conn:
        if severidade and severidade != "Todos":
            rows = conn.execute(
                "SELECT * FROM alertas WHERE severidade=? ORDER BY timestamp DESC",
                (severidade,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alertas ORDER BY CASE severidade "
                "WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 "
                "WHEN 'Médio' THEN 3 ELSE 4 END, timestamp DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def buscar_alerta(aid: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM alertas WHERE id=?", (aid,)).fetchone()
    return dict(row) if row else None


def confirmar_alerta(aid: str, usuario: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE alertas SET status='Confirmado', confirmado_por=? WHERE id=?",
            (usuario, aid)
        )
    registrar_log(usuario, f"Confirmou alerta {aid}")


def escalar_alerta(aid: str, usuario: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE alertas SET status='Escalado', confirmado_por=? WHERE id=?",
            (usuario, aid)
        )
    registrar_log(usuario, f"Escalou alerta {aid} para diretor de missão")


def fechar_alerta(aid: str, usuario: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE alertas SET status='Fechado' WHERE id=?", (aid,)
        )
    registrar_log(usuario, f"Fechou alerta {aid}")


def contagem_alertas():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT severidade, COUNT(*) as total FROM alertas "
            "WHERE status='Ativo' GROUP BY severidade"
        ).fetchall()
    return {r["severidade"]: r["total"] for r in rows}


# ── LOG DE AUDITORIA ──────────────────────────────────────────────────────

def listar_auditoria():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM auditoria ORDER BY id DESC LIMIT 200"
        ).fetchall()
    return [dict(r) for r in rows]


def exportar_auditoria_csv() -> str:
    import csv, io
    rows = listar_auditoria()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["id","timestamp","usuario","acao"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


# ── CONFIGURAÇÕES ─────────────────────────────────────────────────────────

def listar_configs():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM configuracoes").fetchall()
    return {r["chave"]: r["valor"] for r in rows}


def salvar_configs(dados: dict, autor: str):
    with get_conn() as conn:
        for chave, valor in dados.items():
            conn.execute(
                "INSERT OR REPLACE INTO configuracoes VALUES (?,?)",
                (chave, valor)
            )
    registrar_log(autor, "Atualizou configurações da plataforma")


def get_config(chave: str, default=""):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT valor FROM configuracoes WHERE chave=?", (chave,)
        ).fetchone()
    return row["valor"] if row else default


# ── RELATÓRIOS ────────────────────────────────────────────────────────────

def listar_relatorios():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM relatorios ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def salvar_relatorio(tipo, periodo, formato, arquivo, autor):
    data_hora = now()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO relatorios (data_hora,tipo,periodo,formato,arquivo) VALUES (?,?,?,?,?)",
            (data_hora, tipo, periodo, formato, arquivo)
        )
    registrar_log(autor, f"Gerou relatório {tipo} ({periodo}) em formato {formato} — arquivo: {arquivo}")


# ── ANÁLISE PREDITIVA ─────────────────────────────────────────────────────

def analise_preditiva():
    """Calcula previsões simples baseadas no estado atual dos sensores."""
    sensores = listar_sensores()
    previsoes = []
    risco_total = 0.0

    for s in sensores:
        if s["status"] == "Crítico":
            prob = 0.92
            dias = 2
            risco_total += 0.4
        elif s["status"] == "Alto":
            prob = 0.67
            dias = 5
            risco_total += 0.2
        elif s["status"] == "Médio":
            prob = 0.45
            dias = 9
            risco_total += 0.1
        else:
            continue

        from datetime import datetime, timedelta
        previsao_data = (datetime.now() + timedelta(days=dias)).strftime("%d/%m/%Y")
        previsoes.append({
            "sensor":    s["nome"],
            "sensor_id": s["id"],
            "prob":      prob,
            "prob_pct":  f"{int(prob*100)}%",
            "data":      previsao_data,
            "status":    s["status"],
        })

    risco_total = min(risco_total, 1.0)
    nivel = "ALTO" if risco_total > 0.6 else "MÉDIO" if risco_total > 0.3 else "BAIXO"

    return {
        "previsoes":    sorted(previsoes, key=lambda x: -x["prob"]),
        "risco_score":  round(risco_total, 2),
        "risco_nivel":  nivel,
        "total_falhas": len(previsoes),
    }
