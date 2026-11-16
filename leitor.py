"""Leitura de demonstrações financeiras (PDF ou CSV) e conversão para as variáveis do modelo."""
import io
import re
import unicodedata

import pandas as pd

from faixas import MEDIANAS

CAMPOS = [
    "Ativo_Total", "Passivo_Total", "Ativo_Circulante", "Passivo_Circulante",
    "Lucro_Liquido", "Receita_Liquida", "Resultado_Operacional", "Fluxo_Caixa",
    "Indice_Alavancagem", "ROA", "Indice_Capital_Giro",
    "Taxa_Crescimento_PIB", "Taxa_Juros", "Taxa_Inflacao",
]

# Como cada variável pode aparecer escrita no documento (texto já sem acento e em minúsculas)
ROTULOS = {
    "Ativo_Total": r"ativo total|total do ativo(?! circulante)|total de ativos",
    "Passivo_Total": r"passivo total(?! e)|total do passivo(?! e| circulante)|total de passivos",
    "Ativo_Circulante": r"ativo circulante|total do ativo circulante",
    "Passivo_Circulante": r"passivo circulante|total do passivo circulante",
    "Lucro_Liquido": r"lucro liquido|resultado liquido|lucro do exercicio|resultado do exercicio|lucro/prejuizo liquido",
    "Receita_Liquida": r"receita liquida|receita operacional liquida|vendas liquidas|receita de vendas liquida",
    "Resultado_Operacional": r"resultado operacional|lucro operacional|\bebit\b",
    "Fluxo_Caixa": r"fluxo de caixa|fluxo caixa|geracao de caixa|variacao liquida de caixa",
    "Indice_Alavancagem": r"indice de alavancagem|alavancagem|divida\s*/\s*patrimonio",
    "ROA": r"\broa\b|retorno sobre (?:o )?ativo",
    "Indice_Capital_Giro": r"indice de capital de giro|capital de giro|liquidez corrente",
    "Taxa_Crescimento_PIB": r"crescimento do pib|crescimento pib|\bpib\b",
    "Taxa_Juros": r"taxa de juros|taxa selic|\bselic\b|\bjuros\b",
    "Taxa_Inflacao": r"taxa de inflacao|\binflacao\b|\bipca\b",
}

CAMPOS_MOEDA = ["Ativo_Total", "Passivo_Total", "Ativo_Circulante", "Passivo_Circulante",
                "Lucro_Liquido", "Receita_Liquida", "Resultado_Operacional", "Fluxo_Caixa"]
CAMPOS_MACRO = ["Taxa_Crescimento_PIB", "Taxa_Juros", "Taxa_Inflacao"]

SETORES_PALAVRAS = {
    "energy": "Energy", "energia": "Energy",
    "finance": "Finance", "financas": "Finance", "financeiro": "Finance",
    "healthcare": "Healthcare", "saude": "Healthcare",
    "manufacturing": "Manufacturing", "industria": "Manufacturing",
    "retail": "Retail", "varejo": "Retail",
    "technology": "Technology", "tecnologia": "Technology",
}

_NUM = r"(\(?)\s?(-?\s?\d[\d\.]*(?:,\d+)?)\s*(\)?)\s*(%?)"


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
        m = re.search(rf"(?:{rotulo})[^0-9\-\n]{{0,60}}?(?:\n\s*(?:r\$\s*)?)?{_NUM}", t)
        if m:
            valor = converter_numero(m.group(2))
            if valor is not None:
                if m.group(1) == "(" and m.group(3) == ")":  # (1.234,00) = negativo em balanços
                    valor = -abs(valor)
                achados[campo] = _ajustar(campo, valor, m.group(4) == "%")
    return achados


def _detectar_unidade(texto: str) -> tuple[float, str | None]:
    """Detecta se os valores estão em milhares ou milhões de reais."""
    t = normalizar(texto)
    m = re.search(r"\b(?:valores\s+)?(?:em|expressos?\s+em)\s+(?:r\$\s*)?(milhares|milhoes|milhao|mil)\b", t)
    if not m:
        return 1.0, None
    if m.group(1) in ("milhoes", "milhao"):
        return 1e6, "milhões de reais"
    return 1e3, "milhares de reais"


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


def _pacote(achados: dict, setor, nome, unidade: str | None = None) -> dict:
    calculados, padroes = [], []
    a = achados
    if "ROA" not in a and a.get("Ativo_Total") and "Lucro_Liquido" in a:
        a["ROA"] = a["Lucro_Liquido"] / a["Ativo_Total"]
        calculados.append("ROA")
    if "Indice_Capital_Giro" not in a and a.get("Passivo_Circulante") and "Ativo_Circulante" in a:
        a["Indice_Capital_Giro"] = a["Ativo_Circulante"] / a["Passivo_Circulante"]
        calculados.append("Indice_Capital_Giro")
    if "Indice_Alavancagem" not in a and "Passivo_Total" in a and a.get("Ativo_Total", 0) > a["Passivo_Total"]:
        a["Indice_Alavancagem"] = a["Passivo_Total"] / (a["Ativo_Total"] - a["Passivo_Total"])
        calculados.append("Indice_Alavancagem")
    for c in CAMPOS_MACRO:  # cenário macro: valores neutros (mediana do treino) quando o documento não informa
        if c not in a:
            a[c] = MEDIANAS[c]
            padroes.append(c)
    return {
        "dados": a,
        "setor": setor,
        "nome": nome,
        "calculados": calculados,
        "padroes": padroes,
        "unidade": unidade,
        "faltando": [c for c in CAMPOS if c not in a] + ([] if setor else ["Setor"]),
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
    achados = _extrair_do_texto(texto)
    fator, unidade = _detectar_unidade(texto)
    if fator != 1.0:
        for c in CAMPOS_MOEDA:
            if c in achados:
                achados[c] *= fator
    return _pacote(achados, _detectar_setor(texto), _detectar_nome(texto), unidade)


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
