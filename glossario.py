"""Textos explicativos (linguagem simples) e formatação dos indicadores."""

# tipo: moeda (R$), indice (número puro), roa (fração mostrada em %), taxa (já em %)
VARIAVEIS = {
    "Ativo_Total": dict(
        rotulo="Ativo total", tipo="moeda", grupo="Balanço Patrimonial", icone="🏭",
        curta="Tudo o que a empresa possui.",
        longa="Soma de tudo o que a empresa tem: dinheiro em caixa, estoques, máquinas, prédios, "
              "dinheiro a receber de clientes. É o \"tamanho\" da empresa.",
        dica="Sozinho não diz muito: uma empresa grande pode estar saudável ou muito endividada. "
             "Ele ganha sentido quando comparado com o passivo.",
    ),
    "Ativo_Circulante": dict(
        rotulo="Ativo circulante", tipo="moeda", grupo="Balanço Patrimonial", icone="💵",
        curta="O que vira dinheiro em até 1 ano.",
        longa="Parte do ativo que a empresa consegue transformar em dinheiro rapidamente (até 12 meses): "
              "caixa, aplicações, estoque, contas a receber.",
        dica="É o \"dinheiro à mão\" para pagar as contas do curto prazo.",
    ),
    "Passivo_Total": dict(
        rotulo="Passivo total", tipo="moeda", grupo="Balanço Patrimonial", icone="📉",
        curta="Tudo o que a empresa deve.",
        longa="Soma de todas as dívidas e obrigações: empréstimos, fornecedores, impostos, salários a pagar.",
        dica="Quanto mais próximo do ativo total, mais a empresa é financiada por dinheiro de terceiros.",
    ),
    "Passivo_Circulante": dict(
        rotulo="Passivo circulante", tipo="moeda", grupo="Balanço Patrimonial", icone="🧾",
        curta="O que vence em até 1 ano.",
        longa="Dívidas e contas que precisam ser pagas em até 12 meses: fornecedores, parcelas de empréstimos, "
              "impostos e salários.",
        dica="Se for maior que o ativo circulante, a empresa pode ter dificuldade de pagar as contas do próximo ano.",
    ),
    "Receita_Liquida": dict(
        rotulo="Receita líquida", tipo="moeda", grupo="Resultado (DRE)", icone="🛒",
        curta="Quanto a empresa vendeu, já sem impostos sobre vendas.",
        longa="Total de vendas do período, descontados impostos, devoluções e abatimentos. É o dinheiro que "
              "realmente \"entra\" pela atividade da empresa.",
        dica="Receita alta não garante lucro: os custos podem comer tudo.",
    ),
    "Resultado_Operacional": dict(
        rotulo="Resultado operacional", tipo="moeda", grupo="Resultado (DRE)", icone="⚙️",
        curta="Lucro ou prejuízo só com a atividade principal.",
        longa="O que sobra (ou falta) depois de pagar os custos e despesas do dia a dia, antes de juros e "
              "de alguns impostos. Mostra se o negócio em si é rentável.",
        dica="Se for negativo, a empresa perde dinheiro mesmo antes de pagar os juros das dívidas.",
    ),
    "Lucro_Liquido": dict(
        rotulo="Lucro líquido", tipo="moeda", grupo="Resultado (DRE)", icone="💰",
        curta="O que sobrou no fim, depois de pagar tudo.",
        longa="Resultado final do período: receitas menos custos, despesas, juros e impostos. "
              "Positivo é lucro; negativo é prejuízo.",
        dica="Prejuízos repetidos consomem o patrimônio da empresa e são um sinal clássico de alerta.",
    ),
    "Fluxo_Caixa": dict(
        rotulo="Fluxo de caixa", tipo="moeda", grupo="Fluxo de Caixa", icone="🔄",
        curta="Quanto dinheiro de verdade entrou ou saiu.",
        longa="Diferença entre o dinheiro que entrou e o que saiu no período. Uma empresa pode ter lucro "
              "no papel e mesmo assim ficar sem dinheiro no caixa.",
        dica="Fluxo de caixa negativo por muito tempo significa que a empresa está \"queimando\" dinheiro.",
    ),
    "ROA": dict(
        rotulo="ROA (retorno sobre ativos)", tipo="roa", grupo="Indicadores", icone="📈",
        curta="Quanto lucro a empresa gera para cada R$ 100 que tem em ativos.",
        longa="Lucro líquido dividido pelo ativo total. Um ROA de 6% quer dizer que, para cada R$ 100 em "
              "ativos, a empresa gerou R$ 6 de lucro no ano.",
        dica="Negativo = a empresa está dando prejuízo. Quanto maior, mais eficiente ela é em usar o que tem.",
    ),
    "Indice_Capital_Giro": dict(
        rotulo="Índice de capital de giro", tipo="indice", grupo="Indicadores", icone="🔁",
        curta="Consegue pagar as contas de curto prazo?",
        longa="Compara o que a empresa tem para receber/usar no curto prazo (ativo circulante) com o que "
              "precisa pagar no curto prazo (passivo circulante). Valor 2,0 significa R$ 2 disponíveis para "
              "cada R$ 1 de contas a vencer.",
        dica="Abaixo de 1 significa que há mais contas a pagar do que dinheiro disponível: sinal de aperto.",
    ),
    "Indice_Alavancagem": dict(
        rotulo="Índice de alavancagem", tipo="indice", grupo="Indicadores", icone="⚖️",
        curta="O quanto a empresa depende de dívidas.",
        longa="Mede quanto a empresa usa dinheiro emprestado em vez de capital próprio. Quanto maior o "
              "valor, mais endividada ela é e mais frágil fica se as vendas caírem ou os juros subirem.",
        dica="É o indicador que mais pesa na decisão do modelo.",
    ),
    "Taxa_Crescimento_PIB": dict(
        rotulo="Crescimento do PIB", tipo="taxa", grupo="Cenário econômico", icone="🌎",
        curta="Quanto a economia do país cresceu.",
        longa="O PIB é a soma de tudo o que o país produz. Se ele cresce, há mais vendas e emprego; "
              "se cai (recessão), as empresas sofrem.",
        dica="Contexto de fora da empresa: um ano de recessão deixa todo mundo mais vulnerável.",
    ),
    "Taxa_Juros": dict(
        rotulo="Taxa de juros", tipo="taxa", grupo="Cenário econômico", icone="🏦",
        curta="O preço do dinheiro emprestado.",
        longa="Quanto custa pegar dinheiro emprestado na economia. Juros altos encarecem as dívidas e "
              "pesam mais para empresas muito endividadas.",
        dica="Juros altos + dívida alta é uma combinação perigosa.",
    ),
    "Taxa_Inflacao": dict(
        rotulo="Inflação", tipo="taxa", grupo="Cenário econômico", icone="🏷️",
        curta="Quanto os preços subiram.",
        longa="Aumento geral dos preços. Inflação alta eleva os custos da empresa e reduz o poder de "
              "compra dos clientes.",
        dica="Afeta a margem de lucro: os custos sobem e nem sempre dá para repassar ao preço.",
    ),
}

SETORES = {
    "Energy": "Energia", "Finance": "Finanças", "Healthcare": "Saúde",
    "Manufacturing": "Indústria", "Retail": "Varejo", "Technology": "Tecnologia",
}

ORDEM_EXIBICAO = [
    "Ativo_Total", "Ativo_Circulante", "Passivo_Total", "Passivo_Circulante",
    "Receita_Liquida", "Resultado_Operacional", "Lucro_Liquido", "Fluxo_Caixa",
    "ROA", "Indice_Capital_Giro", "Indice_Alavancagem",
    "Taxa_Crescimento_PIB", "Taxa_Juros", "Taxa_Inflacao",
]


def _br(v: float, casas: int = 2) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar(campo: str, v: float) -> str:
    tipo = VARIAVEIS[campo]["tipo"]
    if tipo == "moeda":
        sinal = "-" if v < 0 else ""
        a = abs(v)
        if a >= 1e9:
            return f"{sinal}R$ {_br(a / 1e9)} bi"
        return f"{sinal}R$ {_br(a / 1e6)} mi"
    if tipo == "roa":
        return f"{_br(v * 100)}%"
    if tipo == "taxa":
        return f"{_br(v)}%"
    return _br(v)


def semaforo(campo: str, v: float) -> str:
    """Leitura rápida por regra prática (NÃO é a decisão do modelo)."""
    if campo in ("Lucro_Liquido", "Resultado_Operacional", "Fluxo_Caixa"):
        return "🔴" if v < 0 else "🟢"
    if campo == "ROA":
        return "🔴" if v <= 0 else ("🟡" if v < 0.02 else "🟢")
    if campo == "Indice_Capital_Giro":
        return "🔴" if v < 1 else ("🟡" if v < 1.5 else "🟢")
    if campo == "Indice_Alavancagem":
        return "🔴" if v > 2.5 else ("🟡" if v > 1.5 else "🟢")
    return "⚪"
