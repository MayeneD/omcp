"""
OMCP — Servidor local v4
Uso: python server.py
Acesse: http://localhost:3000

Dependencias para PDF: pip install reportlab
"""

import sys
import json
import urllib.parse
import http.server
import socketserver
import mimetypes
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from data.init_db import init as init_db
from data import db as db_module
from data.db import (
    autenticar, get_config, set_db,
    listar_usuarios, buscar_usuario, criar_usuario, atualizar_usuario, deletar_usuario,
    listar_sensores, buscar_sensor, criar_sensor, atualizar_sensor, deletar_sensor,
    listar_alertas, buscar_alerta, confirmar_alerta, escalar_alerta, fechar_alerta, contagem_alertas,
    listar_auditoria, exportar_auditoria_csv,
    listar_configs, salvar_configs,
    listar_relatorios, salvar_relatorio,
    analise_preditiva,
)

PORT = 3000

# Mapeamento missão → arquivo de banco
DATA_DIR = BASE_DIR / "data"
MISSAO_DB = {
    "LUNA-7":   DATA_DIR / "omcp.db",
    "MARS-3":   DATA_DIR / "mars3.db",
    "ISS-Dock": DATA_DIR / "iss_emergencia.db",
}

PAGES = {
    "/":              "login",
    "/login":         "login",
    "/dashboard":     "dashboard",
    "/alertas":       "alertas",
    "/sensores":      "sensores",
    "/preditiva":     "preditiva",
    "/relatorio":     "relatorio",
    "/usuarios":      "usuarios",
    "/auditoria":     "auditoria",
    "/configuracoes": "configuracoes",
}

TITLES = {
    "login":         "Login",
    "dashboard":     "Dashboard",
    "alertas":       "Alertas",
    "sensores":      "Sensores",
    "preditiva":     "Analise Preditiva",
    "relatorio":     "Relatorios",
    "usuarios":      "Usuarios",
    "auditoria":     "Auditoria",
    "configuracoes": "Configuracoes",
}


def read(path):
    return path.read_text(encoding="utf-8")


def build_page(page_name):
    pages_dir = BASE_DIR / "pages"
    if page_name == "login":
        return read(pages_dir / "login.html")
    base    = read(pages_dir / "_base.html")
    topnav  = read(pages_dir / "_topnav.html")
    modal   = read(pages_dir / "_modal-alert.html")
    content = read(pages_dir / f"{page_name}.html")
    title   = TITLES.get(page_name, "OMCP")
    html = base.replace("{{title}}", title)
    html = html.replace("{{topnav}}", topnav)
    html = html.replace("{{content}}", content)
    html = html.replace("{{modal}}", modal)
    return html


def json_resp(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_resp(handler, html, status=200):
    body = html.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def parse_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length).decode("utf-8")
    ct = handler.headers.get("Content-Type", "")
    if "application/json" in ct:
        return json.loads(raw) if raw else {}
    return dict(urllib.parse.parse_qsl(raw))


class OMCPHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        qs   = urllib.parse.parse_qs(self.path.split("?")[1] if "?" in self.path else "")

        if path in PAGES:
            html_resp(self, build_page(PAGES[path]))
            return

        if path == "/api/usuarios":
            json_resp(self, listar_usuarios()); return
        if path.startswith("/api/usuarios/"):
            uid = path.split("/")[-1]
            u = buscar_usuario(uid)
            json_resp(self, u if u else {"erro": "Nao encontrado"}, 200 if u else 404); return

        if path == "/api/sensores":
            json_resp(self, listar_sensores()); return
        if path.startswith("/api/sensores/"):
            sid = path.split("/")[-1]
            s = buscar_sensor(sid)
            json_resp(self, s if s else {"erro": "Nao encontrado"}, 200 if s else 404); return

        if path == "/api/alertas":
            sev = qs.get("severidade", [None])[0]
            json_resp(self, listar_alertas(sev)); return
        if path == "/api/alertas/contagem":
            json_resp(self, contagem_alertas()); return
        if path.startswith("/api/alertas/"):
            aid = path.split("/")[-1]
            a = buscar_alerta(aid)
            json_resp(self, a if a else {"erro": "Nao encontrado"}, 200 if a else 404); return

        if path == "/api/auditoria":
            json_resp(self, listar_auditoria()); return
        if path == "/api/auditoria/exportar":
            csv_data = exportar_auditoria_csv()
            body = csv_data.encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="omcp_auditoria.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body); return

        if path == "/api/configuracoes":
            json_resp(self, listar_configs()); return

        if path == "/api/missao-ativa":
            from data.db import get_db
            json_resp(self, {
                "missao": get_config("missao_ativa", "LUNA-7"),
                "banco":  get_db().name
            })
            return

        if path == "/api/relatorios":
            json_resp(self, listar_relatorios()); return

        if path == "/api/preditiva":
            json_resp(self, analise_preditiva()); return

        if path.startswith("/relatorios/"):
            nome = path.split("/")[-1]
            fpath = BASE_DIR / "relatorios" / nome
            if fpath.is_file():
                ext = fpath.suffix.lower()
                ct  = "application/pdf" if ext == ".pdf" else "text/csv"
                body = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Disposition", f'attachment; filename="{nome}"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                json_resp(self, {"erro": "Arquivo nao encontrado"}, 404)
            return

        fpath = BASE_DIR / path.lstrip("/")
        if fpath.is_file():
            mime, _ = mimetypes.guess_type(str(fpath))
            mime = mime or "application/octet-stream"
            body = fpath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body); return

        json_resp(self, {"erro": f"Nao encontrado: {path}"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        body = parse_body(self)
        autor = body.get("_autor", get_config("usuario_logado", "sistema"))

        if path == "/api/login":
            user = autenticar(body.get("email",""), body.get("senha",""))
            if user:
                # Troca o banco conforme a missão selecionada
                missao = body.get("missao", "LUNA-7")
                db_path = MISSAO_DB.get(missao, DATA_DIR / "omcp.db")
                if db_path.exists():
                    set_db(db_path)
                    print(f"  ✓ Banco trocado para: {db_path.name} ({missao})")
                else:
                    print(f"  ⚠ Banco {db_path.name} não encontrado, usando omcp.db")
                    set_db(DATA_DIR / "omcp.db")
                salvar_configs({"usuario_logado": user["email"].split("@")[0],
                                "missao_ativa": missao}, "sistema")
                json_resp(self, {"ok": True, "usuario": user, "missao": missao})
            else:
                json_resp(self, {"ok": False, "erro": "Credenciais invalidas"}, 401)
            return

        if path == "/api/usuarios":
            try:
                uid = criar_usuario(body, autor)
                json_resp(self, {"ok": True, "id": uid})
            except Exception as e:
                json_resp(self, {"ok": False, "erro": str(e)}, 400)
            return

        if path == "/api/sensores":
            try:
                sid = criar_sensor(body, autor)
                json_resp(self, {"ok": True, "id": sid})
            except Exception as e:
                json_resp(self, {"ok": False, "erro": str(e)}, 400)
            return

        if "/api/alertas/" in path and path.endswith("/confirmar"):
            aid = path.split("/")[3]
            confirmar_alerta(aid, autor)
            json_resp(self, {"ok": True}); return
        if "/api/alertas/" in path and path.endswith("/escalar"):
            aid = path.split("/")[3]
            escalar_alerta(aid, autor)
            json_resp(self, {"ok": True}); return
        if "/api/alertas/" in path and path.endswith("/fechar"):
            aid = path.split("/")[3]
            fechar_alerta(aid, autor)
            json_resp(self, {"ok": True}); return

        if path == "/api/configuracoes":
            salvar_configs(body, autor)
            json_resp(self, {"ok": True}); return

        if path == "/api/relatorios/gerar":
            tipo    = body.get("tipo", "Preditiva")
            periodo = body.get("periodo", "7 dias")
            formato = body.get("formato", "PDF").upper()
            missao  = get_config("missao_ativa", "LUNA-7")
            try:
                if formato == "CSV":
                    if "Alerta" in tipo:
                        dados = listar_alertas()
                        cols  = ["id","titulo","severidade","valor","timestamp","status"]
                    elif "Status" in tipo:
                        dados = listar_sensores()
                        cols  = ["id","nome","tipo","leitura","unidade","limiar_min","limiar_max","status"]
                    elif "Auditoria" in tipo:
                        dados = listar_auditoria()
                        cols  = ["id","timestamp","usuario","acao"]
                    else:
                        dados = listar_sensores()
                        cols  = ["id","nome","tipo","leitura","unidade","status"]
                    from data.pdf_gen import gerar_csv
                    nome_arq = gerar_csv(tipo, dados, cols)
                else:
                    from data.pdf_gen import gerar_pdf_preditiva, gerar_pdf_alertas, gerar_pdf_status
                    if "Alerta" in tipo:
                        nome_arq = gerar_pdf_alertas(listar_alertas(), missao)
                    elif "Status" in tipo:
                        nome_arq = gerar_pdf_status(listar_sensores(), missao)
                    else:
                        nome_arq = gerar_pdf_preditiva(analise_preditiva(), missao)
                salvar_relatorio(tipo, periodo, formato, nome_arq, autor)
                json_resp(self, {"ok": True, "arquivo": nome_arq, "url": f"/relatorios/{nome_arq}"})
            except ImportError:
                json_resp(self, {"ok": False, "erro": "reportlab nao instalado. Execute: pip install reportlab"}, 500)
            except Exception as e:
                json_resp(self, {"ok": False, "erro": str(e)}, 500)
            return

        json_resp(self, {"erro": f"Rota POST nao encontrada: {path}"}, 404)

    def do_PUT(self):
        path = self.path.split("?")[0].rstrip("/")
        body = parse_body(self)
        autor = body.get("_autor", get_config("usuario_logado", "sistema"))

        if path.startswith("/api/usuarios/"):
            uid = path.split("/")[-1]
            try:
                atualizar_usuario(uid, body, autor)
                json_resp(self, {"ok": True})
            except Exception as e:
                json_resp(self, {"ok": False, "erro": str(e)}, 400)
            return

        if path.startswith("/api/sensores/"):
            sid = path.split("/")[-1]
            try:
                atualizar_sensor(sid, body, autor)
                json_resp(self, {"ok": True})
            except Exception as e:
                json_resp(self, {"ok": False, "erro": str(e)}, 400)
            return

        json_resp(self, {"erro": f"Rota PUT nao encontrada: {path}"}, 404)

    def do_DELETE(self):
        path  = self.path.split("?")[0].rstrip("/")
        qs    = urllib.parse.parse_qs(self.path.split("?")[1] if "?" in self.path else "")
        autor = qs.get("autor", [get_config("usuario_logado", "sistema")])[0]

        if path.startswith("/api/usuarios/"):
            uid = path.split("/")[-1]
            deletar_usuario(uid, autor)
            json_resp(self, {"ok": True}); return

        if path.startswith("/api/sensores/"):
            sid = path.split("/")[-1]
            deletar_sensor(sid, autor)
            json_resp(self, {"ok": True}); return

        json_resp(self, {"erro": f"Rota DELETE nao encontrada: {path}"}, 404)

    def log_message(self, format, *args):
        pass

    def log_request(self, code="-", size="-"):
        if not str(code).startswith("2"):
            print(f"  [{code}] {self.path}")


def main():
    init_db()
    (BASE_DIR / "relatorios").mkdir(exist_ok=True)
    with socketserver.TCPServer(("", PORT), OMCPHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"\n  🛰️  OMCP v4 rodando em http://localhost:{PORT}")
        print(f"  Para PDF: pip install reportlab")
        print(f"  Ctrl+C para parar\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Servidor encerrado.\n")


if __name__ == "__main__":
    main()
