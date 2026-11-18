import io
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st
import xgboost as xgb

from empresas_exemplo import EMPRESAS
from glossario import ORDEM_EXIBICAO, SETORES, VARIAVEIS, formatar, semaforo
from faixas import confianca
from leitor import CAMPOS, ler_arquivo
from validacao import validar

BASE = Path(__file__).parent
MODEL_PATH = BASE / "modelo_xgboost.pkl"
PASTA_EXEMPLOS = BASE / "exemplos"

st.set_page_config(page_title="Análise de Risco Financeiro", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .hero {background: linear-gradient(120deg,#0F172A,#1D4ED8); color:#fff; padding:1.6rem 1.8rem;
           border-radius:16px; margin-bottom:1rem;}
    .hero h1 {color:#fff; margin:0 0 .3rem 0; font-size:2rem;}
    .hero p {color:#DBEAFE; margin:0; font-size:1.02rem;}
    .card {padding:1.3rem 1.5rem; border-radius:16px; border:1px solid;}
    .card h2 {margin:0 0 .3rem 0; font-size:1.7rem;}
    .card p {margin:0; font-size:1rem;}
    .barra {position:relative; height:16px; border-radius:99px; margin:1.6rem 0 .3rem 0;
            background:linear-gradient(90deg,#22C55E 0%,#FACC15 50%,#EF4444 100%);}
    .marca {position:absolute; top:-7px; width:6px; height:30px; background:#0F172A;
            border-radius:3px; border:2px solid #fff;}
    .legenda {display:flex; justify-content:space-between; font-size:.8rem; color:#475569;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- modelo
if not MODEL_PATH.exists():
    st.error("O arquivo modelo_xgboost.pkl não foi encontrado na mesma pasta do app.py.")
    st.stop()


@st.cache_resource
def carregar_modelo():
    return joblib.load(MODEL_PATH)


try:
    modelo = carregar_modelo()
except Exception as exc:  # noqa: BLE001
    st.error(f"Não foi possível carregar o modelo: {exc}")
    st.stop()

COLUNAS = [str(c) for c in modelo.feature_names_in_]
DUMMIES = [c for c in COLUNAS if c.startswith("Setor_Industria_")]


def montar_x(dados: dict, setor: str) -> pd.DataFrame:
    """Reproduz o pd.get_dummies(drop_first=True): Energy é a categoria de referência."""
    linha = {c: float(dados[c]) for c in CAMPOS}
    for d in DUMMIES:
        linha[d] = 0.0
    if setor != "Energy":
        linha[f"Setor_Industria_{setor}"] = 1.0
    return pd.DataFrame([[linha[c] for c in COLUNAS]], columns=COLUNAS)


def probabilidade(dados: dict, setor: str) -> float:
    X = montar_x(dados, setor)
    return float(modelo.predict_proba(X)[0][list(modelo.classes_).index(1)])


def contribuicoes(dados: dict, setor: str) -> dict:
    """Quanto cada informação empurrou a decisão (valores SHAP nativos do XGBoost)."""
    X = montar_x(dados, setor)
    dm = xgb.DMatrix(X, feature_names=COLUNAS)
    c = modelo.get_booster().predict(dm, pred_contribs=True)[0]
    out = {}
    for nome, v in zip(COLUNAS, c[:-1]):
        chave = "Setor" if nome in DUMMIES else nome
        out[chave] = out.get(chave, 0.0) + float(v)
    return out


def rotulo(chave: str) -> str:
    return "Setor da empresa" if chave == "Setor" else VARIAVEIS[chave]["rotulo"]


def pdf_exemplo(emp: dict):
    """Devolve (nome, bytes) do PDF da empresa; se a pasta exemplos faltar, gera o PDF na hora."""
    nome = f"{emp['arquivo']}.pdf"
    caminho = PASTA_EXEMPLOS / nome
    if caminho.exists():
        return nome, caminho.read_bytes()
    try:
        from gerar_exemplos import gerar
        buf = io.BytesIO()
        gerar(emp, buf)
        return nome, buf.getvalue()
    except Exception:  # noqa: BLE001
        return nome, None


def _num_lote(v) -> float | None:
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def ler_lote_csv(raw_bytes: bytes) -> pd.DataFrame:
    """Lê um CSV tabular com várias empresas (1 por linha) e calcula o ranking comparativo de risco."""
    texto = raw_bytes.decode("utf-8-sig", errors="replace")
    sep = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
    df = pd.read_csv(io.StringIO(texto), sep=sep)
    df.columns = [c.strip() for c in df.columns]

    # Sinônimos aceitos para colunas de CSVs externos
    SINONIMOS = {
        "Receita_Liquida": ["Receita_Liquida", "Receita_Vendas", "Receita", "Faturamento"],
        "Fluxo_Caixa": ["Fluxo_Caixa", "Fluxo_Caixa_Operacional", "FCO"],
        "Resultado_Operacional": ["Resultado_Operacional", "EBIT", "Lucro_Operacional"],
        "Taxa_Crescimento_PIB": ["Taxa_Crescimento_PIB", "PIB"],
    }

    macro_def = {
        k: float(EMPRESAS[0][k])
        for k in ("Taxa_Crescimento_PIB", "Taxa_Juros", "Taxa_Inflacao")
        if k in EMPRESAS[0]
    }

    resultados = []
    for idx, row in df.iterrows():
        nome_emp = str(row["Empresa"]).strip() if "Empresa" in df.columns and pd.notna(row["Empresa"]) else f"Empresa {idx + 1}"
        setor = str(row["Setor"]).strip() if "Setor" in df.columns and pd.notna(row["Setor"]) else "Energy"
        if setor not in SETORES:
            setor = "Energy"

        dados = {}
        for c in CAMPOS:
            candidatos = SINONIMOS.get(c, [c])
            for col_cand in candidatos:
                if col_cand in df.columns:
                    val = _num_lote(row[col_cand])
                    if val is not None:
                        dados[c] = val
                        break

        # Estima Resultado_Operacional se vier Lucro_Liquido + Despesas_Juros
        if "Resultado_Operacional" not in dados and "Lucro_Liquido" in dados:
            juros = _num_lote(row["Despesas_Juros"]) if "Despesas_Juros" in df.columns else 0.0
            dados["Resultado_Operacional"] = dados["Lucro_Liquido"] + (juros or 0.0)

        if "ROA" not in dados and dados.get("Ativo_Total") and "Lucro_Liquido" in dados:
            dados["ROA"] = dados["Lucro_Liquido"] / dados["Ativo_Total"]
        if "Indice_Capital_Giro" not in dados and dados.get("Passivo_Circulante") and "Ativo_Circulante" in dados:
            dados["Indice_Capital_Giro"] = dados["Ativo_Circulante"] / dados["Passivo_Circulante"]
        if "Indice_Alavancagem" not in dados and dados.get("Ativo_Total") and dados.get("Passivo_Total") is not None:
            pl = dados["Ativo_Total"] - dados["Passivo_Total"]
            if pl > 0:
                dados["Indice_Alavancagem"] = dados["Passivo_Total"] / pl

        for m, val in macro_def.items():
            dados.setdefault(m, val)

        faltando = [c for c in CAMPOS if c not in dados]
        if faltando:
            resultados.append({
                "Empresa": nome_emp,
                "Setor": SETORES.get(setor, setor),
                "Classificação": f"⚠️ Faltando: {', '.join(faltando)}",
                "Probabilidade de Falência": None,
                "ROA": None,
                "Alavancagem": None,
                "Capital de Giro": None,
                "Lucro Líquido": None,
                "Ativo Total": None,
            })
            continue

        prob = probabilidade(dados, setor)
        alto = int(modelo.predict(montar_x(dados, setor))[0]) == 1
        resultados.append({
            "Empresa": nome_emp,
            "Setor": SETORES.get(setor, setor),
            "Classificação": "🔴 Alto Risco" if alto else "🟢 Baixo Risco",
            "Probabilidade de Falência": prob,
            "ROA": dados["ROA"],
            "Alavancagem": dados["Indice_Alavancagem"],
            "Capital de Giro": dados["Indice_Capital_Giro"],
            "Lucro Líquido": dados["Lucro_Liquido"],
            "Ativo Total": dados["Ativo_Total"],
        })

    res_df = pd.DataFrame(resultados)
    return res_df.sort_values(by="Probabilidade de Falência", ascending=False, na_position="last").reset_index(drop=True)


# ---------------------------------------------------------------- estado
S = st.session_state
S.setdefault("dados", None)
S.setdefault("setor", None)
S.setdefault("nome", None)
S.setdefault("faltando", [])
S.setdefault("calculados", [])
S.setdefault("padroes", [])
S.setdefault("unidade", None)
S.setdefault("analisado", False)
S.setdefault("token", 0)
S.setdefault("lote", None)


def carregar(pacote: dict, analisar: bool = False):
    S.dados = pacote["dados"]
    S.setor = pacote["setor"]
    S.nome = pacote.get("nome")
    S.faltando = pacote["faltando"]
    S.calculados = pacote.get("calculados", [])
    S.padroes = pacote.get("padroes", [])
    S.unidade = pacote.get("unidade")
    S.analisado = analisar
    S.lote = None
    S.token += 1


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Sobre o projeto")
    st.write("**Modelo:** XGBoost")
    st.write("**Objetivo:** classificar empresas em baixo ou alto risco de falência.")
    st.write("**Classes:**")
    st.write("- 0 — Baixo risco\n- 1 — Alto risco")
    st.divider()
    st.subheader("Como usar")
    st.markdown(
        "1. Escolha a origem dos dados\n"
        "2. Confira o que foi lido\n"
        "3. Clique em **Analisar**\n"
        "4. Veja o resultado"
    )
    st.divider()
    st.caption("Projeto Integrador V — Ciência de Dados. Aluno: Rafael Marques Mansano.")

st.markdown(
    """
    <div class="hero">
      <h1>📊 Análise de Risco Financeiro</h1>
      <p>Envie a demonstração financeira de uma empresa (ou um CSV com várias empresas) e veja, em segundos,
      se o modelo de Machine Learning as considera de <b>baixo</b> ou <b>alto risco</b> de falência — e por quê.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_an, tab_glos, tab_sobre = st.tabs(["🔍 Analisar empresa", "📚 Glossário", "🧠 Sobre o modelo"])

# ================================================================ ABA 1
with tab_an:
    st.subheader("1. De onde vêm os dados da empresa?")
    origem = st.radio(
        "Origem",
        ["📄 Enviar demonstração financeira", "🧪 Usar uma empresa de exemplo", "✍️ Preencher manualmente"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ---------- upload
    if origem.startswith("📄"):
        st.caption(
            "Aceita PDF com texto selecionável ou CSV (individual ou **em lote**, com várias empresas — uma por linha). "
            "O app reconhece nomes comuns de contas (ex.: \"Total do Ativo\", \"Resultado do Exercício\"), "
            "valores entre parênteses como negativos e unidades em milhares ou milhões de reais. "
            "Indicadores que faltarem (ROA, capital de giro, alavancagem) são calculados."
        )
        arq = st.file_uploader("Demonstração financeira", type=["pdf", "csv"], label_visibility="collapsed")
        if arq is not None and S.get("arq_id") != arq.file_id:
            try:
                is_lote = False
                if arq.name.lower().endswith(".csv"):
                    linhas_arq = [l for l in arq.getvalue().decode("utf-8-sig", errors="replace").splitlines() if l.strip()]
                    cab = linhas_arq[0] if linhas_arq else ""
                    if ("Empresa" in cab and "Ativo_Total" in cab) or len(linhas_arq) > 25:
                        is_lote = True

                if is_lote:
                    S.lote = ler_lote_csv(arq.getvalue())
                    S.dados = None
                    S.analisado = False
                    S.arq_id = arq.file_id
                    st.toast(f"Lote com {len(S.lote)} empresas processado!", icon="✅")
                else:
                    carregar(ler_arquivo(arq.name, arq.getvalue()))
                    S.arq_id = arq.file_id
                    st.toast("Documento lido com sucesso!", icon="✅")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Não consegui ler o arquivo: {exc}")

        with st.expander("Não tem um documento? Baixe um modelo ou use os exemplos"):
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                modelo_csv = "indicador,valor\nSetor,Technology\n" + "\n".join(
                    f"{VARIAVEIS[c]['rotulo']}," for c in ORDEM_EXIBICAO
                )
                st.download_button("⬇️ Modelo de CSV em branco", modelo_csv, "modelo_demonstracao.csv", "text/csv", use_container_width=True)
            with c_m2:
                modelo_lote = ",".join(["Empresa", "Setor"] + CAMPOS) + "\n"
                st.download_button("⬇️ Modelo de CSV em lote", modelo_lote, "modelo_lote.csv", "text/csv", use_container_width=True)
            st.caption("Ou escolha **Usar uma empresa de exemplo** acima: lá você baixa os PDFs prontos.")

        # ---------- COMPARATIVO DE VÁRIAS EMPRESAS EM LOTE (CSV)
        if S.lote is not None:
            st.divider()
            st.subheader("2. Comparativo de Risco entre Empresas (Análise em Lote)")
            df_lote = S.lote
            df_validas = df_lote.dropna(subset=["Probabilidade de Falência"]).copy()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total de empresas", len(df_lote))
            m2.metric("🔴 Alto Risco", int((df_lote["Classificação"] == "🔴 Alto Risco").sum()))
            m3.metric("🟢 Baixo Risco", int((df_lote["Classificação"] == "🟢 Baixo Risco").sum()))
            prob_media = df_validas["Probabilidade de Falência"].mean() if not df_validas.empty else 0.0
            m4.metric("Risco Médio do Lote", f"{prob_media:.1%}")

            # Tabela comparativa formatada
            df_vis = df_lote.copy()
            df_vis["Probabilidade de Falência"] = df_vis["Probabilidade de Falência"].apply(
                lambda x: f"{x:.1%}" if pd.notna(x) else "—"
            )
            df_vis["ROA"] = df_vis["ROA"].apply(
                lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "—"
            )
            df_vis["Alavancagem"] = df_vis["Alavancagem"].apply(
                lambda x: f"{x:.2f}x" if pd.notna(x) else "—"
            )
            df_vis["Capital de Giro"] = df_vis["Capital de Giro"].apply(
                lambda x: f"{x:.2f}x" if pd.notna(x) else "—"
            )
            df_vis["Lucro Líquido"] = df_vis["Lucro Líquido"].apply(
                lambda x: formatar("Lucro_Liquido", x) if pd.notna(x) else "—"
            )
            df_vis["Ativo Total"] = df_vis["Ativo Total"].apply(
                lambda x: formatar("Ativo_Total", x) if pd.notna(x) else "—"
            )
            st.dataframe(df_vis, hide_index=True, use_container_width=True)

            # Gráficos comparativos entre empresas
            if not df_validas.empty:
                st.markdown("#### 📊 Gráficos Comparativos")
                g1, g2 = st.columns(2)
                with g1:
                    chart_risco = (
                        alt.Chart(df_validas)
                        .mark_bar()
                        .encode(
                            x=alt.X("Probabilidade de Falência:Q", axis=alt.Axis(format="%"), title="Probabilidade de Falência"),
                            y=alt.Y("Empresa:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                            color=alt.Color(
                                "Classificação:N",
                                scale=alt.Scale(
                                    domain=["🔴 Alto Risco", "🟢 Baixo Risco"],
                                    range=["#DC2626", "#16A34A"],
                                ),
                                legend=alt.Legend(title="Classificação", orient="bottom"),
                            ),
                            tooltip=[
                                "Empresa",
                                "Setor",
                                "Classificação",
                                alt.Tooltip("Probabilidade de Falência:Q", format=".1%"),
                                alt.Tooltip("ROA:Q", format=".2%"),
                                alt.Tooltip("Alavancagem:Q", format=".2f"),
                            ],
                        )
                        .properties(title="Ranking de Probabilidade de Risco", height=max(260, 32 * len(df_validas)))
                    )
                    st.altair_chart(chart_risco, use_container_width=True)

                with g2:
                    chart_disp = (
                        alt.Chart(df_validas)
                        .mark_circle(size=140)
                        .encode(
                            x=alt.X("Alavancagem:Q", title="Índice de Alavancagem (Dívida / PL)"),
                            y=alt.Y("ROA:Q", axis=alt.Axis(format="%"), title="ROA (Retorno sobre Ativo)"),
                            color=alt.Color(
                                "Classificação:N",
                                scale=alt.Scale(
                                    domain=["🔴 Alto Risco", "🟢 Baixo Risco"],
                                    range=["#DC2626", "#16A34A"],
                                ),
                                legend=None,
                            ),
                            tooltip=[
                                "Empresa",
                                "Setor",
                                alt.Tooltip("Probabilidade de Falência:Q", format=".1%"),
                                alt.Tooltip("ROA:Q", format=".2%"),
                                alt.Tooltip("Alavancagem:Q", format=".2f"),
                                alt.Tooltip("Capital de Giro:Q", format=".2f"),
                            ],
                        )
                        .properties(title="Rentabilidade (ROA) vs. Alavancagem", height=max(260, 32 * len(df_validas)))
                    )
                    st.altair_chart(chart_disp, use_container_width=True)

            st.download_button(
                "⬇️ Baixar comparativo completo (CSV)",
                df_lote.to_csv(index=False).encode("utf-8-sig"),
                "comparativo_risco_empresas.csv",
                "text/csv",
                type="primary",
            )

    # ---------- exemplos
    elif origem.startswith("🧪"):
        st.caption("Quatro empresas fictícias, com documentos prontos. Carregue direto ou baixe o PDF para testar o upload.")
        nomes = [e["nome"] for e in EMPRESAS]
        escolhida = st.selectbox(
            "Empresa", nomes,
            format_func=lambda n: f"{n} — {SETORES[next(e['setor'] for e in EMPRESAS if e['nome'] == n)]}",
        )
        emp = next(e for e in EMPRESAS if e["nome"] == escolhida)
        pdf_nome, pdf_bytes = pdf_exemplo(emp)
        if pdf_bytes is None:
            st.error("Não encontrei o PDF deste exemplo. Confira se a pasta 'exemplos' e o arquivo "
                     "'gerar_exemplos.py' foram enviados ao repositório.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📥 Carregar esta empresa", type="primary", use_container_width=True):
                    carregar(ler_arquivo(pdf_nome, pdf_bytes))
                    st.rerun()
            with c2:
                st.download_button("⬇️ Baixar o PDF desta empresa", pdf_bytes, pdf_nome,
                                   "application/pdf", use_container_width=True)

    # ---------- manual
    else:
        st.caption("Valores em **milhões de reais** (ex.: 412,3 = R$ 412,3 milhões). Já vêm preenchidos com um exemplo.")
        base = {**EMPRESAS[3], **(S.dados or {})}
        setor_base = S.setor or "Energy"
        with st.form("form_manual"):
            valores = {}
            grupos = {}
            for c in ORDEM_EXIBICAO:
                grupos.setdefault(VARIAVEIS[c]["grupo"], []).append(c)
            auto = st.checkbox("Calcular ROA e capital de giro automaticamente", value=True,
                               help="ROA = lucro líquido ÷ ativo total; capital de giro = ativo circulante ÷ passivo circulante.")
            auto_alav = st.checkbox("Calcular a alavancagem automaticamente (dívida ÷ patrimônio líquido)", value=False,
                                    help="Usa passivo total ÷ (ativo total − passivo total).")
            for grupo, campos in grupos.items():
                st.markdown(f"**{grupo}**")
                colunas = st.columns(3)
                for i, c in enumerate(campos):
                    v = VARIAVEIS[c]
                    with colunas[i % 3]:
                        if v["tipo"] == "moeda":
                            x = st.number_input(f"{v['icone']} {v['rotulo']} (R$ mi)", value=float(base[c]) / 1e6,
                                                step=1.0, format="%.2f", help=v["curta"], key=f"m_{c}_{S.token}")
                            valores[c] = x * 1e6
                        elif v["tipo"] == "roa":
                            x = st.number_input(f"{v['icone']} {v['rotulo']} (%)", value=float(base[c]) * 100,
                                                step=0.1, format="%.2f", help=v["curta"], key=f"m_{c}_{S.token}")
                            valores[c] = x / 100
                        elif v["tipo"] == "taxa":
                            valores[c] = st.number_input(f"{v['icone']} {v['rotulo']} (%)", value=float(base[c]),
                                                         step=0.1, format="%.2f", help=v["curta"], key=f"m_{c}_{S.token}")
                        else:
                            valores[c] = st.number_input(f"{v['icone']} {v['rotulo']}", value=float(base[c]),
                                                         step=0.05, format="%.2f", help=v["curta"], key=f"m_{c}_{S.token}")
            st.markdown("**Setor da empresa**")
            setor_sel = st.selectbox("Setor", list(SETORES), index=list(SETORES).index(setor_base),
                                     format_func=lambda s: f"{SETORES[s]} ({s})", label_visibility="collapsed")
            ok = st.form_submit_button("🔍 Analisar risco desta empresa", type="primary", use_container_width=True)
        if ok:
            if auto:
                if valores["Ativo_Total"]:
                    valores["ROA"] = valores["Lucro_Liquido"] / valores["Ativo_Total"]
                if valores["Passivo_Circulante"]:
                    valores["Indice_Capital_Giro"] = valores["Ativo_Circulante"] / valores["Passivo_Circulante"]
            if auto_alav and valores["Ativo_Total"] > valores["Passivo_Total"]:
                valores["Indice_Alavancagem"] = valores["Passivo_Total"] / (valores["Ativo_Total"] - valores["Passivo_Total"])
            carregar({"dados": valores, "setor": setor_sel, "nome": "Empresa informada manualmente", "faltando": [],
                      "calculados": [], "padroes": [], "unidade": None},
                     analisar=True)
            st.rerun()

    # ---------- passo 2: dados lidos
    if S.dados:
        st.divider()
        st.subheader("2. Dados identificados")
        if S.nome:
            st.markdown(f"**Empresa:** {S.nome}  \n**Setor:** {SETORES.get(S.setor, '— não identificado —')}")
        if S.unidade:
            st.info(f"O documento informa valores em **{S.unidade}**. Converti tudo para reais automaticamente.")
        if S.faltando:
            nomes_faltando = [("Setor" if f == "Setor" else VARIAVEIS[f]["rotulo"]) for f in S.faltando]
            st.warning(
                "Não encontrei no documento: **" + ", ".join(nomes_faltando) + "**. "
                "Vá em **Preencher manualmente**: o que foi lido já vem preenchido e você completa o resto."
            )
        if S.calculados:
            st.caption("🧮 Calculados automaticamente a partir de outros valores do documento: "
                       + ", ".join(VARIAVEIS[c]["rotulo"] for c in S.calculados) + ".")
        if S.padroes:
            st.info("⚙️ O cenário macroeconômico (" + ", ".join(VARIAVEIS[c]["rotulo"] for c in S.padroes)
                    + ") não constava no documento. Usei **valores neutros** (os mais comuns na base de treinamento). "
                    "Para informar os valores reais do período, use **Preencher manualmente**: os dados atuais já vêm preenchidos.")

        linhas = [
            {"": semaforo(c, S.dados[c]), "Indicador": VARIAVEIS[c]["rotulo"],
             "Valor": formatar(c, S.dados[c]),
             "Em palavras simples": VARIAVEIS[c]["curta"]}
            for c in ORDEM_EXIBICAO if c in S.dados
        ]
        st.dataframe(pd.DataFrame(linhas), hide_index=True, height=35 * (len(linhas) + 1) + 3)
        st.caption("🟢 sinal saudável · 🟡 atenção · 🔴 sinal de alerta · ⚪ sem regra prática (leitura rápida por regras gerais de finanças).")

        problemas = validar(S.dados) if not S.faltando else []
        tem_erro = any(n == "erro" for n, _ in problemas)
        for nivel, msg in problemas:
            (st.error if nivel == "erro" else st.warning)(msg)

        if st.button("🔍 Analisar risco desta empresa", type="primary", disabled=bool(S.faltando) or tem_erro):
            S.analisado = True

    # ---------- passo 3: resultado
    if S.dados and S.analisado and not S.faltando and not tem_erro:
        dados, setor = S.dados, S.setor
        prob = probabilidade(dados, setor)
        alto = int(modelo.predict(montar_x(dados, setor))[0]) == 1

        st.divider()
        st.subheader("3. Resultado da análise")
        cor_fundo, cor_borda, cor_txt = ("#FEF2F2", "#FCA5A5", "#991B1B") if alto else ("#F0FDF4", "#86EFAC", "#166534")
        titulo = "🔴 ALTO RISCO de falência" if alto else "🟢 BAIXO RISCO de falência"
        texto = (
            "O perfil financeiro desta empresa se parece com o de empresas que enfrentaram dificuldades graves "
            "nos dados usados no treinamento."
            if alto else
            "O perfil financeiro desta empresa se parece com o de empresas financeiramente estáveis "
            "nos dados usados no treinamento."
        )
        esq, dir_ = st.columns([3, 2])
        with esq:
            st.markdown(
                f'<div class="card" style="background:{cor_fundo};border-color:{cor_borda};color:{cor_txt}">'
                f"<h2>{titulo}</h2><p>{texto}</p></div>",
                unsafe_allow_html=True,
            )
        nivel_conf, fora, extremos = confianca(dados)
        with dir_:
            st.metric("Probabilidade estimada de alto risco", f"{prob:.1%}")
            st.metric("Confiança da previsão", nivel_conf,
                      help="Alta: todos os valores estão na faixa que o modelo conheceu no treinamento. "
                           "Média/Baixa: alguns valores estão fora dessa faixa, então o modelo precisa extrapolar.")
        st.markdown(
            f'<div class="barra"><div class="marca" style="left:calc({min(max(prob * 100, 1.0), 98.5):.1f}% - 3px)"></div></div>'
            '<div class="legenda"><span>0% — muito seguro</span><span>50%</span><span>100% — muito arriscado</span></div>',
            unsafe_allow_html=True,
        )
        if fora:
            st.warning(
                "**Atenção:** estes valores estão fora da faixa de empresas que o modelo conheceu no treinamento: "
                + ", ".join(VARIAVEIS[c]["rotulo"] for c in fora)
                + ". Nesses casos o modelo precisa extrapolar e a previsão é **menos confiável**."
            )
        if 0.3 <= prob <= 0.7:
            st.info("A probabilidade está numa **zona de incerteza** (entre 30% e 70%): o modelo não tem muita "
                    "convicção neste caso. Vale olhar com mais cuidado os indicadores.")

        # ----- por quê?
        st.markdown("#### Por que o modelo chegou a essa conclusão?")
        contrib = contribuicoes(dados, setor)
        ordenado = sorted(contrib.items(), key=lambda kv: abs(kv[1]), reverse=True)
        topo = ordenado[:3]
        for chave, v in topo:
            valor_txt = "" if chave == "Setor" else f" ({formatar(chave, dados[chave])})"
            seta = "🔺 empurrou para **alto risco**" if v > 0 else "🔻 puxou para **baixo risco**"
            st.markdown(f"- **{rotulo(chave)}**{valor_txt}: {seta}")

        graf = pd.DataFrame(
            [{"Informação": rotulo(k), "Peso": v,
              "Efeito": "Aumenta o risco" if v > 0 else "Reduz o risco"} for k, v in ordenado[:8]]
        )
        chart = (
            alt.Chart(graf)
            .mark_bar()
            .encode(
                x=alt.X("Peso:Q", title="← reduz o risco   |   aumenta o risco →"),
                y=alt.Y("Informação:N", sort=None, title=None, axis=alt.Axis(labelLimit=300)),
                color=alt.Color("Efeito:N", legend=None,
                                scale=alt.Scale(domain=["Aumenta o risco", "Reduz o risco"],
                                                range=["#DC2626", "#16A34A"])),
                tooltip=["Informação", "Efeito", alt.Tooltip("Peso:Q", format=".2f")],
            )
            .properties(height=300)
        )
        st.altair_chart(chart)
        st.caption("Cada barra mostra o quanto aquela informação deslocou a decisão do modelo para um lado ou para o outro "
                   "(são os valores SHAP calculados pelo próprio XGBoost).")

        st.caption("⚠️ A probabilidade é uma estimativa do modelo, não uma garantia de que a empresa irá ou não falir.")

# ================================================================ ABA 2
with tab_glos:
    st.subheader("O que significa cada informação?")
    st.write("Explicações simples, sem economês. Abra cada item para ver o significado e como interpretar.")
    grupos = {}
    for c in ORDEM_EXIBICAO:
        grupos.setdefault(VARIAVEIS[c]["grupo"], []).append(c)
    for grupo, campos in grupos.items():
        st.markdown(f"##### {grupo}")
        for c in campos:
            v = VARIAVEIS[c]
            with st.expander(f"{v['icone']} {v['rotulo']} — {v['curta']}"):
                st.write(v["longa"])
                st.markdown(f"💡 **Como interpretar:** {v['dica']}")
    st.markdown("##### Setor da empresa")
    with st.expander("🏢 Setor — o ramo de atuação"):
        st.write("O modelo conhece seis setores: " + ", ".join(f"{pt} ({en})" for en, pt in SETORES.items()) + ". "
                 "Cada setor tem riscos próprios. Tecnicamente, *Energy* é a categoria de referência: "
                 "quando ela é escolhida, as demais marcações de setor ficam zeradas.")

# ================================================================ ABA 3
with tab_sobre:
    st.subheader("Como o modelo funciona (sem complicação)")
    n_arv = modelo.get_params().get("n_estimators")
    prof = modelo.get_params().get("max_depth")
    st.markdown(
        f"O modelo é um **XGBoost**: um comitê de **{n_arv} árvores de decisão** pequenas (cada uma com até "
        f"{prof} níveis de perguntas, como *\"a alavancagem é maior que 2,5?\"*). As árvores são treinadas "
        "em sequência e **cada nova árvore tenta corrigir os erros das anteriores**. No fim, os votos de todas "
        "são somados e viram uma probabilidade de a empresa ser de alto risco."
    )
    st.markdown("**Quais informações mais pesam, em geral?**")
    imp = {}
    for nome, v in zip(COLUNAS, modelo.feature_importances_):
        chave = "Setor" if nome in DUMMIES else nome
        imp[chave] = imp.get(chave, 0.0) + float(v)
    df_imp = pd.DataFrame(sorted(imp.items(), key=lambda kv: kv[1], reverse=True), columns=["k", "Importância"])
    df_imp["Informação"] = df_imp["k"].map(rotulo)
    graf_imp = (
        alt.Chart(df_imp.head(10))
        .mark_bar(color="#1D4ED8")
        .encode(x=alt.X("Importância:Q", axis=alt.Axis(format="%"), title="Importância no modelo"),
                y=alt.Y("Informação:N", sort=None, title=None, axis=alt.Axis(labelLimit=300)),
                tooltip=["Informação", alt.Tooltip("Importância:Q", format=".1%")])
        .properties(height=320)
    )
    st.altair_chart(graf_imp)
