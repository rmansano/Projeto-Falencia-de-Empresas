"""Faixas de valores vistas no treinamento do modelo: (mínimo, percentil 1%, mediana, percentil 99%, máximo)."""

FAIXAS = {
    "Ativo_Total": (1178336.36, 10438539.64, 504767142.62, 988877277.11, 999975998.27),
    "Passivo_Total": (176429.94, 1708197.20, 154539818.95, 699021127.54, 789463392.58),
    "Ativo_Circulante": (118830.46, 981960.70, 92657223.29, 424945893.41, 492527436.75),
    "Passivo_Circulante": (107386.82, 255602.89, 34645633.59, 306568951.68, 435916697.79),
    "Lucro_Liquido": (-993966.83, -665312.05, 37417384.95, 170316557.75, 194152002.91),
    "Receita_Liquida": (103075.33, 753260.38, 92060764.14, 418048661.50, 493002805.90),
    "Resultado_Operacional": (10238.73, 135753.14, 14380164.33, 96559412.76, 140899968.43),
    "Fluxo_Caixa": (-1023462.81, -666166.83, 37376499.30, 170271208.18, 194096831.87),
    "Indice_Alavancagem": (0.00, 0.01, 0.75, 3.82, 3.99),
    "ROA": (-0.63, -0.01, 0.10, 0.20, 0.20),
    "Indice_Capital_Giro": (1.00, 1.01, 1.94, 82.53, 896.08),
    "Taxa_Crescimento_PIB": (-5.00, -4.88, 2.52, 9.84, 10.00),
    "Taxa_Juros": (0.50, 0.56, 5.18, 9.88, 10.00),
    "Taxa_Inflacao": (1.00, 1.08, 4.45, 7.92, 8.00),
}

MEDIANAS = {c: f[2] for c, f in FAIXAS.items()}


def avaliar_faixa(campo: str, valor: float) -> str:
    """'ok', 'extremo' (dentro do visto, mas raro) ou 'abaixo'/'acima' (fora do que o modelo conhece)."""
    mn, p1, _, p99, mx = FAIXAS[campo]
    if valor < mn:
        return "abaixo"
    if valor > mx:
        return "acima"
    if valor < p1 or valor > p99:
        return "extremo"
    return "ok"


def confianca(dados: dict) -> tuple[str, list[str], list[str]]:
    """Devolve (nível de confiança, campos fora da faixa, campos extremos)."""
    fora = [c for c in FAIXAS if c in dados and avaliar_faixa(c, dados[c]) in ("abaixo", "acima")]
    extremos = [c for c in FAIXAS if c in dados and avaliar_faixa(c, dados[c]) == "extremo"]
    if not fora and len(extremos) <= 1:
        nivel = "Alta"
    elif len(fora) <= 2:
        nivel = "Média"
    else:
        nivel = "Baixa"
    return nivel, fora, extremos
