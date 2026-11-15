"""Leitura de demonstrações financeiras (PDF ou CSV) e conversão para as variáveis do modelo."""
import io
import re
import unicodedata

import pandas as pd

CAMPOS = [
    "Ativo_Total", "Passivo_Total", "Ativo_Circulante", "Passivo_Circulante",
    "Lucro_Liquido", "Receita_Liquida", "Resultado_Operacional", "Fluxo_Caixa",
    "Indice_Alavancagem", "ROA", "Indice_Capital_Giro",
    "Taxa_Crescimento_PIB", "Taxa_Juros", "Taxa_Inflacao",
]

# Como cada variável pode aparecer escrita no documento (texto já sem acento e em minúsculas)
ROTULOS = {
    "Ativo_Total": r"ativo total",
    "Passivo_Total": r"passivo total",
    "Ativo_Circulante": r"ativo circulante",
    "Passivo_Circulante": r"passivo circulante",
    "Lucro_Liquido": r"lucro liquido",
    "Receita_Liquida": r"receita liquida",
    "Resultado_Operacional": r"resultado operacional",
    "Fluxo_Caixa": r"fluxo de caixa|fluxo caixa",
    "Indice_Alavancagem": r"indice de alavancagem|alavancagem",
    "ROA": r"\broa\b",
    "Indice_Capital_Giro": r"indice de capital de giro|capital de giro",
    "Taxa_Crescimento_PIB": r"crescimento do pib|crescimento pib|\bpib\b",
    "Taxa_Juros": r"taxa de juros|\bjuros\b",
    "Taxa_Inflacao": r"taxa de inflacao|\binflacao\b",
}

SETORES_PALAVRAS = {
    "energy": "Energy", "energia": "Energy",
    "finance": "Finance", "financas": "Finance", "financeiro": "Finance",
    "healthcare": "Healthcare", "saude": "Healthcare",
    "manufacturing": "Manufacturing", "industria": "Manufacturing",
    "retail": "Retail", "varejo": "Retail",
    "technology": "Technology", "tecnologia": "Technology",
}

_NUM = r"(-?\s?\d[\d\.]*(?:,\d+)?)\s*(%?)"


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().replace("_", " ")
    return re.sub(r"[ \t]+", " ", texto)


def converter_numero(txt) -> float | None:
    """Aceita '1.234.567,89', '1234567.89', '-12,5', '3,40'."""
    if isinstance(txt, (int, float)):
        return float(txt)
    s = str(txt).replace("R$", "").replace("%", "").replace(" ", "").strip()
    if not s:
        return None
    try:
        if "," in s:
            return float(s.replace(".", "").replace(",", "."))
        if s.count(".") > 1:
            return float(s.replace(".", ""))
        if s.count(".") == 1:
            antes, depois = s.split(".")
            if depois.isdigit() and len(depois) == 3 and antes.lstrip("-").isdigit() \
                    and len(antes.lstrip("-")) <= 3:
                return float(antes + depois)  # 412.300 -> milhar
        return float(s)
    except ValueError:
        return None


def _ajustar(campo: str, valor: float, tinha_percentual: bool) -> float:
    # O modelo trabalha com ROA em fração (0,06) e com as taxas em pontos percentuais (4,5)
    if campo == "ROA" and (tinha_percentual or abs(valor) > 1):
        return valor / 100
    return valor


def _extrair_do_texto(texto: str) -> dict:
    t = normalizar(texto)
    achados = {}
    for campo, rotulo in ROTULOS.items():
        m = re.search(rf"(?:{rotulo})[^0-9\-]{{0,60}}?{_NUM}", t)
        if m:
            valor = converter_numero(m.group(1))
            if valor is not None:
                achados[campo] = _ajustar(campo, valor, m.group(2) == "%")
    return achados


def _detectar_setor(texto: str) -> str | None:
    t = normalizar(texto)
    i = t.find("setor")
    trecho = t[i:i + 90] if i >= 0 else ""
    for palavra, setor in SETORES_PALAVRAS.items():
        if re.search(rf"\b{palavra}\b", trecho):
            return setor
    return None


def _detectar_nome(texto: str) -> str | None:
    m = re.search(r"\n\s*([^\n|]+?)\s*\|\s*CNPJ", "\n" + texto)
    return m.group(1).strip() if m else None


def _pacote(achados: dict, setor, nome) -> dict:
    return {
        "dados": achados,
        "setor": setor,
        "nome": nome,
        "faltando": [c for c in CAMPOS if c not in achados] + ([] if setor else ["Setor"]),
    }


def ler_pdf(arquivo) -> dict:
    from pypdf import PdfReader

    leitor = PdfReader(arquivo)
    texto = "\n".join((p.extract_text() or "") for p in leitor.pages)
    if len(texto.strip()) < 30:
        raise ValueError(
            "Não consegui ler texto neste PDF (ele pode ser uma imagem escaneada). "
            "Use um PDF com texto selecionável ou preencha manualmente."
        )
    return _pacote(_extrair_do_texto(texto), _detectar_setor(texto), _detectar_nome(texto))


def ler_csv(conteudo: bytes) -> dict:
    df = pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python", dtype=str)
    df = df.dropna(how="all")
    colunas = {normalizar(c).strip(): c for c in df.columns}
    achados, setor, nome = {}, None, None

    # Formato 1: uma coluna por variável (igual ao dataset), usa a primeira linha
    if sum(normalizar(c) in colunas for c in CAMPOS) >= 5:
        linha = df.iloc[0]
        for c in CAMPOS:
            col = colunas.get(normalizar(c))
            if col is not None:
                v = converter_numero(linha[col])
                if v is not None:
                    achados[c] = _ajustar(c, v, "%" in str(linha[col]))
        for k, col in colunas.items():
            if k.startswith("setor"):
                setor = _detectar_setor("setor " + str(linha[col]))
            if k in ("empresa", "nome"):
                nome = str(linha[col])
    # Formato 2: duas colunas (indicador, valor)
    else:
        for _, linha in df.iterrows():
            rotulo, valor = normalizar(linha.iloc[0]), str(linha.iloc[1])
            if rotulo.startswith("setor"):
                setor = _detectar_setor("setor " + valor)
                continue
            if rotulo in ("empresa", "nome"):
                nome = valor
                continue
            for c, padrao in ROTULOS.items():
                if re.search(padrao, rotulo):
                    v = converter_numero(valor)
                    if v is not None:
                        achados[c] = _ajustar(c, v, "%" in valor)
                    break
    return _pacote(achados, setor, nome)


def ler_arquivo(nome_arquivo: str, conteudo: bytes) -> dict:
    ext = nome_arquivo.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return ler_pdf(io.BytesIO(conteudo))
    if ext in ("csv", "txt"):
        return ler_csv(conteudo)
    raise ValueError("Formato não suportado. Envie um PDF ou um CSV.")
