"""Gera os PDFs de demonstração financeira fictícia em ./exemplos"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from empresas_exemplo import EMPRESAS

SETOR_PT = {"Energy": "Energy (Energia)", "Finance": "Finance (Finanças)",
            "Healthcare": "Healthcare (Saúde)", "Manufacturing": "Manufacturing (Indústria)",
            "Retail": "Retail (Varejo)", "Technology": "Technology (Tecnologia)"}

def brl(v):
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {'-' if v < 0 else ''}{s}"

def pct(v):
    return f"{v:.2f}".replace(".", ",") + "%"

def num(v):
    return f"{v:.2f}".replace(".", ",")

def tabela(linhas):
    t = Table(linhas, colWidths=[10.5*cm, 6*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t

def gerar(e, destino):
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=18, textColor=colors.HexColor("#0F172A"))
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=colors.HexColor("#1D4ED8"), spaceBefore=12)
    pn = ss["BodyText"]
    doc = SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm,
                            title=f"Demonstrações Financeiras - {e['nome']}")
    el = [
        Paragraph("Demonstrações Financeiras Consolidadas", h1),
        Paragraph(f"<b>{e['nome']}</b> &nbsp;|&nbsp; CNPJ {e['cnpj']} &nbsp;|&nbsp; Exercício {e['exercicio']}", pn),
        Paragraph(f"Setor de atuação: {SETOR_PT[e['setor']]}", pn),
        Paragraph("<i>Documento fictício, criado apenas para demonstração acadêmica.</i>", pn),
        Paragraph("1. Balanço Patrimonial", h2),
        tabela([["Ativo Total", brl(e["Ativo_Total"])],
                ["Ativo Circulante", brl(e["Ativo_Circulante"])],
                ["Passivo Total", brl(e["Passivo_Total"])],
                ["Passivo Circulante", brl(e["Passivo_Circulante"])]]),
        Paragraph("2. Demonstração do Resultado do Exercício (DRE)", h2),
        tabela([["Receita Líquida", brl(e["Receita_Liquida"])],
                ["Resultado Operacional", brl(e["Resultado_Operacional"])],
                ["Lucro Líquido", brl(e["Lucro_Liquido"])]]),
        Paragraph("3. Demonstração do Fluxo de Caixa", h2),
        tabela([["Fluxo de Caixa", brl(e["Fluxo_Caixa"])]]),
        Paragraph("4. Indicadores Financeiros", h2),
        tabela([["ROA (Retorno sobre Ativos)", pct(e["ROA"] * 100)],
                ["Índice de Capital de Giro", num(e["Indice_Capital_Giro"])],
                ["Índice de Alavancagem", num(e["Indice_Alavancagem"])]]),
        Paragraph("5. Cenário Macroeconômico do Período", h2),
        tabela([["Taxa de Crescimento do PIB", pct(e["Taxa_Crescimento_PIB"])],
                ["Taxa de Juros", pct(e["Taxa_Juros"])],
                ["Taxa de Inflação", pct(e["Taxa_Inflacao"])]]),
    ]
    doc.build(el)

if __name__ == "__main__":
    pasta = Path(__file__).parent / "exemplos"
    pasta.mkdir(exist_ok=True)
    for e in EMPRESAS:
        gerar(e, pasta / f"{e['arquivo']}.pdf")
        print("ok", e["arquivo"])
