"""Checagens de coerência dos dados informados. Devolve lista de (nível, mensagem)."""
from glossario import VARIAVEIS, formatar


def _r(c):
    return VARIAVEIS[c]["rotulo"]


def validar(d: dict) -> list[tuple[str, str]]:
    p = []
    g = d.get
    for c in ("Ativo_Total", "Passivo_Total", "Ativo_Circulante", "Passivo_Circulante"):
        if c in d and d[c] < 0:
            p.append(("erro", f"**{_r(c)}** está negativo ({formatar(c, d[c])}). Esse valor não pode ser negativo."))
    if g("Ativo_Total", 1) == 0:
        p.append(("erro", "O **ativo total** está zerado; não é possível analisar a empresa."))

    if "Ativo_Circulante" in d and "Ativo_Total" in d and d["Ativo_Circulante"] > d["Ativo_Total"]:
        p.append(("aviso", "O **ativo circulante** é maior que o **ativo total**. Confira se os valores não foram trocados."))
    if "Passivo_Circulante" in d and "Passivo_Total" in d and d["Passivo_Circulante"] > d["Passivo_Total"]:
        p.append(("aviso", "O **passivo circulante** é maior que o **passivo total**. Confira os valores."))
    if "Passivo_Total" in d and "Ativo_Total" in d and d["Passivo_Total"] > d["Ativo_Total"] > 0:
        p.append(("aviso", "O **passivo total** é maior que o **ativo total**: o patrimônio líquido é negativo "
                           "(a empresa deve mais do que possui). Isso é um sinal de alerta forte."))

    if "ROA" in d and d.get("Ativo_Total") and "Lucro_Liquido" in d:
        esperado = d["Lucro_Liquido"] / d["Ativo_Total"]
        if abs(esperado - d["ROA"]) > 0.005:
            p.append(("aviso", f"O **ROA** informado ({formatar('ROA', d['ROA'])}) não bate com lucro líquido ÷ ativo total "
                               f"({formatar('ROA', esperado)}). Pode haver erro de digitação ou de unidade."))
    if "Indice_Capital_Giro" in d and d.get("Passivo_Circulante") and "Ativo_Circulante" in d:
        esperado = d["Ativo_Circulante"] / d["Passivo_Circulante"]
        if abs(esperado - d["Indice_Capital_Giro"]) > 0.05 * max(esperado, 1):
            p.append(("aviso", f"O **capital de giro** informado ({formatar('Indice_Capital_Giro', d['Indice_Capital_Giro'])}) "
                               f"não bate com ativo circulante ÷ passivo circulante ({formatar('Indice_Capital_Giro', esperado)})."))

    if 0 < g("Ativo_Total", 1e9) < 1e5:
        p.append(("aviso", "Os valores em reais parecem **muito pequenos**. O documento pode estar em milhares ou milhões "
                           "de reais: confira a unidade."))
    for c in ("Taxa_Juros", "Taxa_Inflacao"):
        if c in d and (d[c] > 100 or d[c] < 0):
            p.append(("aviso", f"**{_r(c)}** ({formatar(c, d[c])}) parece fora do normal. Informe em pontos percentuais (ex.: 5 para 5%)."))
    if "Taxa_Crescimento_PIB" in d and abs(d["Taxa_Crescimento_PIB"]) > 30:
        p.append(("aviso", "O **crescimento do PIB** parece fora do normal. Informe em pontos percentuais (ex.: 2,5 para 2,5%)."))
    if "ROA" in d and abs(d["ROA"]) > 1:
        p.append(("aviso", "O **ROA** deve estar em fração (0,06 = 6%). Confira se não foi informado em %."))
    return p
