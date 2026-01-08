import streamlit as st
import json
import collections
import math

# Ranks e valores (como antes)
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {r: i+1 for i, r in enumerate(RANKS)}  # A=1, K=13

# Arquivo histórico
HIST_FILE = 'historico_fs.json'

# Funções load/save, add_rodada, get_winner, análises e sugestao_aposta (cole as que eu dei antes aqui no topo do arquivo)
# Ajuste add_rodada pra usar no input texto:
def add_rodada(historico, home, away):
    if home not in RANKS or away not in RANKS:
        raise ValueError("Rank inválido!")
    historico.append([home, away])
    save_historico(historico)

# Inicializa session_state
if 'historico' not in st.session_state:
    st.session_state.historico = load_historico()
if 'entradas_hoje' not in st.session_state:
    st.session_state.entradas_hoje = 0  # Contador diário

st.title("Football Studio Analyzer")

# Nova seção: Input texto rápido pra digitar direto "K-Q"
st.subheader("➕ Adicionar rodada (texto rápido)")
input_rapido = st.text_input("Digite Home-Away (ex: K-Q ou 9-J):", key="input_rapido")
if st.button("Adicionar via texto"):
    if input_rapido:
        try:
            home, away = input_rapido.upper().split('-')
            add_rodada(st.session_state.historico, home.strip(), away.strip())
            st.success(f"Rodada adicionada: {home} x {away}")
        except:
            st.error("Formato inválido! Use 'Home-Away' como 'K-Q'.")

# Seção de botões rápidos genéricos (opcionais, com exemplos neutros)
st.subheader("➕ Adicionar rodada rápida (Genérica)")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 Home (ex: Q-10)"):
        st.session_state.historico.append(["Q", "10"])
        save_historico(st.session_state.historico)
        st.success("Rodada adicionada: Q-10 (Home vence)")

with col2:
    if st.button("🔵 Away (ex: 10-Q)"):
        st.session_state.historico.append(["10", "Q"])
        save_historico(st.session_state.historico)
        st.success("Rodada adicionada: 10-Q (Away vence)")

with col3:
    if st.button("🟡 Tie (ex: Q-Q)"):
        st.session_state.historico.append(["Q", "Q"])
        save_historico(st.session_state.historico)
        st.success("Rodada adicionada: Q-Q (Tie)")

# Seção manual (mantida, pra precisão)
st.divider()

st.subheader("➕ Adicionar rodada (manual)")

c1, c2 = st.columns(2)

with c1:
    home = st.selectbox("Home", RANKS, key="home_rank")

with c2:
    away = st.selectbox("Away", RANKS, key="away_rank")

if st.button("Adicionar rodada manual"):
    st.session_state.historico.append([home, away])
    save_historico(st.session_state.historico)
    st.success(f"Rodada adicionada: {home} x {away}")

# Limite diário
st.divider()
st.subheader("📊 Controle Diário")
st.write(f"Entradas hoje: {st.session_state.entradas_hoje} / 5")
if st.button("Resetar contador diário"):
    st.session_state.entradas_hoje = 0
    st.success("Contador resetado!")

# Análise e sugestão
if st.button("Analisar e Sugerir Aposta"):
    if st.session_state.entradas_hoje < 5:
        sugestao = sugestao_aposta(st.session_state.historico)
        st.info(sugestao)
        st.session_state.entradas_hoje += 1
    else:
        st.warning("Limite diário atingido! Resete se necessário.")

# Histórico recente
st.divider()
st.subheader("📜 Histórico Recente (últimas 5)")
for rod in st.session_state.historico[-5:]:
    st.write(f"{rod[0]} - {rod[1]} → {get_winner(rod[0], rod[1])}")
