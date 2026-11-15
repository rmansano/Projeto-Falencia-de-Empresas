"""Dados das 4 empresas fictícias usadas nas demonstrações financeiras de exemplo."""

EMPRESAS = [
    dict(
        arquivo="01_Varejo_Horizonte_ALTO_RISCO",
        nome="Varejo Horizonte S.A.", setor="Retail", cnpj="12.345.678/0001-90",
        exercicio=2025,
        Ativo_Total=412_300_000.00, Passivo_Total=318_700_000.00,
        Ativo_Circulante=96_400_000.00, Passivo_Circulante=141_800_000.00,
        Receita_Liquida=187_500_000.00, Resultado_Operacional=-9_800_000.00,
        Lucro_Liquido=-18_200_000.00, Fluxo_Caixa=-12_600_000.00,
        Indice_Alavancagem=3.40, Taxa_Crescimento_PIB=1.20,
        Taxa_Juros=8.50, Taxa_Inflacao=6.90,
    ),
    dict(
        arquivo="02_Metalurgica_Vale_Verde_ALTO_RISCO",
        nome="Metalúrgica Vale Verde Ltda.", setor="Manufacturing", cnpj="23.456.789/0001-01",
        exercicio=2025,
        Ativo_Total=655_000_000.00, Passivo_Total=498_000_000.00,
        Ativo_Circulante=148_000_000.00, Passivo_Circulante=205_000_000.00,
        Receita_Liquida=231_000_000.00, Resultado_Operacional=4_100_000.00,
        Lucro_Liquido=-3_900_000.00, Fluxo_Caixa=-5_200_000.00,
        Indice_Alavancagem=3.10, Taxa_Crescimento_PIB=0.80,
        Taxa_Juros=8.00, Taxa_Inflacao=6.20,
    ),
    dict(
        arquivo="03_TechNuvem_Solucoes_BAIXO_RISCO",
        nome="TechNuvem Soluções S.A.", setor="Technology", cnpj="34.567.890/0001-12",
        exercicio=2025,
        Ativo_Total=380_000_000.00, Passivo_Total=142_000_000.00,
        Ativo_Circulante=168_000_000.00, Passivo_Circulante=54_000_000.00,
        Receita_Liquida=295_000_000.00, Resultado_Operacional=58_000_000.00,
        Lucro_Liquido=45_600_000.00, Fluxo_Caixa=51_300_000.00,
        Indice_Alavancagem=0.90, Taxa_Crescimento_PIB=3.40,
        Taxa_Juros=4.20, Taxa_Inflacao=3.50,
    ),
    dict(
        arquivo="04_Energia_Sol_Nascente_BAIXO_RISCO",
        nome="Energia Sol Nascente S.A.", setor="Energy", cnpj="45.678.901/0001-23",
        exercicio=2025,
        Ativo_Total=870_000_000.00, Passivo_Total=455_000_000.00,
        Ativo_Circulante=190_000_000.00, Passivo_Circulante=98_000_000.00,
        Receita_Liquida=342_000_000.00, Resultado_Operacional=71_000_000.00,
        Lucro_Liquido=52_200_000.00, Fluxo_Caixa=63_800_000.00,
        Indice_Alavancagem=1.60, Taxa_Crescimento_PIB=2.90,
        Taxa_Juros=5.00, Taxa_Inflacao=4.10,
    ),
]

for e in EMPRESAS:
    e["ROA"] = round(e["Lucro_Liquido"] / e["Ativo_Total"], 4)
    e["Indice_Capital_Giro"] = round(e["Ativo_Circulante"] / e["Passivo_Circulante"], 2)
