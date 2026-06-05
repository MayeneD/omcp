"""
Gerador de relatórios PDF usando reportlab.
Instale com: pip install reportlab
"""
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "relatorios"
REPORTS_DIR.mkdir(exist_ok=True)


def _nome_arquivo(tipo: str, formato: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = formato.lower()
    slug = tipo.lower().replace(" ", "_")
    return f"omcp_{slug}_{ts}.{ext}"


def gerar_csv(tipo: str, dados: list, colunas: list) -> str:
    import csv, io
    nome = _nome_arquivo(tipo, "csv")
    path = REPORTS_DIR / nome
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        w.writerows(dados)
    return nome


def gerar_pdf_preditiva(analise: dict, missao: str) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    nome = _nome_arquivo("preditiva", "pdf")
    path = REPORTS_DIR / nome

    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    AZUL   = colors.HexColor("#3b82c4")
    CINZA  = colors.HexColor("#5a85a0")
    VERM   = colors.HexColor("#dc2626")
    VERDE  = colors.HexColor("#3aaa7c")
    AMARELO= colors.HexColor("#d97706")
    BGCARD = colors.HexColor("#f7fafd")

    titulo_style = ParagraphStyle("titulo", fontSize=20, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceAfter=4)
    sub_style    = ParagraphStyle("sub",    fontSize=9,  textColor=CINZA,
                                  fontName="Helvetica",  spaceAfter=12)
    h2_style     = ParagraphStyle("h2",    fontSize=13, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    body_style   = ParagraphStyle("body",  fontSize=9,  textColor=colors.HexColor("#1e3a5f"),
                                  fontName="Helvetica",  spaceAfter=4, leading=14)

    story = []

    # Cabeçalho
    story.append(Paragraph("OMCP — Relatório de Análise Preditiva", titulo_style))
    story.append(Paragraph(
        f"Missão: {missao} &nbsp;|&nbsp; Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL))
    story.append(Spacer(1, 0.4*cm))

    # Resumo executivo
    story.append(Paragraph("Resumo Executivo", h2_style))
    nivel = analise["risco_nivel"]
    cor_nivel = VERM if nivel == "ALTO" else AMARELO if nivel == "MÉDIO" else VERDE
    resumo_data = [
        ["Risco Geral da Missão", nivel],
        ["Score de Risco",        str(analise["risco_score"]) + " / 1.0"],
        ["Falhas Previstas (7d)", str(analise["total_falhas"])],
        ["Precisão do Modelo ML", "96.2%"],
    ]
    t = Table(resumo_data, colWidths=[9*cm, 7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), BGCARD),
        ("BACKGROUND",  (0,1), (-1,1), BGCARD),
        ("BACKGROUND",  (0,2), (-1,2), BGCARD),
        ("BACKGROUND",  (0,3), (-1,3), BGCARD),
        ("TEXTCOLOR",   (0,0), (0,-1), CINZA),
        ("TEXTCOLOR",   (1,0), (1,0), cor_nivel),
        ("TEXTCOLOR",   (1,1), (1,-1), colors.HexColor("#1e3a5f")),
        ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",    (1,0), (1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[BGCARD, colors.white]),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#d6e4f0")),
        ("TOPPADDING",  (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Previsões de falha
    story.append(Paragraph("Previsões de Falha — Próximos 7 Dias", h2_style))

    if analise["previsoes"]:
        header = [["Sensor", "Probabilidade", "Previsão", "Severidade"]]
        rows = [[
            p["sensor"], p["prob_pct"], p["data"], p["status"]
        ] for p in analise["previsoes"]]

        t2 = Table(header + rows, colWidths=[8*cm, 4*cm, 4*cm, 3.5*cm])

        def cor_sev(s):
            return VERM if s=="Crítico" else AMARELO if s=="Alto" else colors.HexColor("#d97706")

        row_styles = [
            ("BACKGROUND", (0,0), (-1,0), AZUL),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#d6e4f0")),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING",(0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, BGCARD]),
        ]
        for i, p in enumerate(analise["previsoes"]):
            row_styles.append(("TEXTCOLOR", (1, i+1), (1, i+1),
                               VERM if p["prob"] > 0.8 else AMARELO))
            row_styles.append(("TEXTCOLOR", (3, i+1), (3, i+1), cor_sev(p["status"])))
            row_styles.append(("FONTNAME",  (1, i+1), (1, i+1), "Helvetica-Bold"))

        t2.setStyle(TableStyle(row_styles))
        story.append(t2)
    else:
        story.append(Paragraph("Nenhuma falha prevista para os próximos 7 dias.", body_style))

    story.append(Spacer(1, 0.5*cm))

    # Recomendações
    story.append(Paragraph("Recomendações Operacionais", h2_style))
    recomendacoes = []
    for p in analise["previsoes"]:
        if p["status"] == "Crítico":
            recomendacoes.append(f"• <b>Intervenção imediata</b> no sensor {p['sensor_id']} — probabilidade de falha {p['prob_pct']} em {p['data']}.")
        elif p["status"] == "Alto":
            recomendacoes.append(f"• <b>Monitoramento reforçado</b> do sensor {p['sensor_id']} — verificar em até 48h.")
        else:
            recomendacoes.append(f"• Acompanhar sensor {p['sensor_id']} nas próximas leituras.")

    if not recomendacoes:
        recomendacoes = ["• Sistema operando dentro dos parâmetros normais. Manter monitoramento de rotina."]

    for r in recomendacoes:
        story.append(Paragraph(r, body_style))

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d6e4f0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Documento gerado automaticamente pelo OMCP v4.0 · {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC · FIAP Aerospace Systems",
        ParagraphStyle("rodape", fontSize=7, textColor=CINZA, fontName="Helvetica")
    ))

    doc.build(story)
    return nome


def gerar_pdf_alertas(alertas: list, missao: str) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    nome = _nome_arquivo("alertas", "pdf")
    path = REPORTS_DIR / nome

    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    AZUL  = colors.HexColor("#3b82c4")
    CINZA = colors.HexColor("#5a85a0")
    VERM  = colors.HexColor("#dc2626")
    BGCARD= colors.HexColor("#f7fafd")

    titulo_style = ParagraphStyle("titulo", fontSize=20, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceAfter=4)
    sub_style    = ParagraphStyle("sub", fontSize=9, textColor=CINZA,
                                  fontName="Helvetica", spaceAfter=12)
    h2_style     = ParagraphStyle("h2", fontSize=13, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)

    story = []
    story.append(Paragraph("OMCP — Relatório de Alertas", titulo_style))
    story.append(Paragraph(
        f"Missão: {missao} &nbsp;|&nbsp; Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Histórico de Alertas", h2_style))

    header = [["ID", "Título", "Severidade", "Valor", "Timestamp", "Status"]]
    rows   = [[a["id"], a["titulo"][:45]+"…" if len(a["titulo"])>45 else a["titulo"],
               a["severidade"], a["valor"], a["timestamp"], a["status"]]
              for a in alertas]

    def cor_sev(s):
        return VERM if s=="Crítico" else colors.HexColor("#ea7c00") if s=="Alto" \
               else colors.HexColor("#d97706") if s=="Médio" else colors.HexColor("#3aaa7c")

    t = Table(header + rows, colWidths=[2.5*cm, 7*cm, 2.5*cm, 2.5*cm, 3.5*cm, 2.5*cm])
    row_styles = [
        ("BACKGROUND",   (0,0), (-1,0), AZUL),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#d6e4f0")),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, BGCARD]),
    ]
    for i, a in enumerate(alertas):
        row_styles.append(("TEXTCOLOR", (2, i+1), (2, i+1), cor_sev(a["severidade"])))
        row_styles.append(("FONTNAME",  (2, i+1), (2, i+1), "Helvetica-Bold"))

    t.setStyle(TableStyle(row_styles))
    story.append(t)

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d6e4f0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"OMCP v4.0 · {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC · FIAP Aerospace Systems",
        ParagraphStyle("rodape", fontSize=7, textColor=CINZA, fontName="Helvetica")
    ))
    doc.build(story)
    return nome


def gerar_pdf_status(sensores: list, missao: str) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    nome = _nome_arquivo("status", "pdf")
    path = REPORTS_DIR / nome

    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    AZUL  = colors.HexColor("#3b82c4")
    CINZA = colors.HexColor("#5a85a0")
    BGCARD= colors.HexColor("#f7fafd")

    titulo_style = ParagraphStyle("titulo", fontSize=20, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceAfter=4)
    sub_style    = ParagraphStyle("sub", fontSize=9, textColor=CINZA,
                                  fontName="Helvetica", spaceAfter=12)
    h2_style     = ParagraphStyle("h2", fontSize=13, textColor=AZUL,
                                  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)

    story = []
    story.append(Paragraph("OMCP — Relatório de Status dos Subsistemas", titulo_style))
    story.append(Paragraph(
        f"Missão: {missao} &nbsp;|&nbsp; Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Status dos Sensores", h2_style))

    header = [["ID", "Nome", "Tipo", "Leitura", "Unidade", "Limiar Mín", "Limiar Máx", "Status"]]
    rows   = [[s["id"], s["nome"], s["tipo"], str(s["leitura"]),
               s["unidade"], str(s["limiar_min"]), str(s["limiar_max"]), s["status"]]
              for s in sensores]

    def cor_sev(s):
        return colors.HexColor("#dc2626") if s=="Crítico" \
               else colors.HexColor("#ea7c00") if s=="Alto" \
               else colors.HexColor("#d97706") if s=="Médio" \
               else colors.HexColor("#3aaa7c")

    t = Table(header + rows, colWidths=[2.8*cm, 4*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm])
    row_styles = [
        ("BACKGROUND",   (0,0), (-1,0), AZUL),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#d6e4f0")),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, BGCARD]),
    ]
    for i, s in enumerate(sensores):
        row_styles.append(("TEXTCOLOR", (7, i+1), (7, i+1), cor_sev(s["status"])))
        row_styles.append(("FONTNAME",  (7, i+1), (7, i+1), "Helvetica-Bold"))
    t.setStyle(TableStyle(row_styles))
    story.append(t)

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d6e4f0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"OMCP v4.0 · {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC · FIAP Aerospace Systems",
        ParagraphStyle("rodape", fontSize=7, textColor=CINZA, fontName="Helvetica")
    ))
    doc.build(story)
    return nome
