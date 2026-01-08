import streamlit as st
import json
import collections
import math

# ==================== CONFIGURAÇÕES E FUNÇÕES AUXILIARES ====================

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {r: i+1 for i, r in enumerate(RANKS)}  # A=1, K=13

HIST_FILE = 'historico_fs.json'

def load_historico():
    try:
        with open(HIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_historico(historico):
    with open(HIST_FILE, 'w') as f:
        json.dump(historico, f)

def get_winner(home, away):
    h_val = RANK_VALUES[home]
    a_val = RANK_VALUES[away]
    if h_val > a_val:
        return 'Home'
    elif h_val < a_val:
        return 'Away'
    else:
        return 'Tie'

# Análises (mesmas que eu passei antes)
def detect_streaks(historico):
    if not historico:
        return []
    winners = [get_winner(h, a) for h, a in historico]
    streaks = []
    current = winners[0]
    count = 1
    for w in winners[1:]:
        if w == current:
            count += 1
        else:
            streaks.append((current, count))
            current = w
            count = 1
    streaks.append((current, count))
    return streaks

def markov_prob(historico):
    if len(historico) < 2:
        return {}
    transitions = collections.defaultdict(lambda: collections.Counter())
    for i in range(1, len(historico)):
        prev = get_winner(*historico[i-1])
        curr = get_winner(*historico[i])
        transitions[prev][curr] += 1
    last = get_winner(*historico[-1])
    total = sum(transitions[last].values())
    if total == 0:
        return {}
    probs = {k: v / total for k, v in transitions[last].items()}
    return probs

def sugestao_aposta(historico):
    if len(historico) < 5:
        return "⚠️ Histórico muito curto. Adicione mais rodadas para análise confiável."
    
    streaks = detect_streaks(historico)
    probs = markov_prob(historico)
    
    sugestao = None
    confianca = 0
    
    # Regra 1: Streak longa → apostar contra
    if streaks and streaks[-1][1] >= 3:
        last_winner = streaks[-1][0]
        sugestao = 'Away' if last_winner == 'Home' else 'Home'
        confianca = 65 + (streaks[-1][1] - 3) * 8
    
    # Regra 2: Markov
    elif probs:
        sugestao = max(probs, key=probs.get)
        confianca = int(probs[sugestao] * 100)
    
    else:
        return "⚠️ Sem padrão detectado ainda."
    
    confianca = min(confianca, 95)
    if confianca < 60:
        return "⚠️ Confiança baixa. Melhor esperar."
    
    return f"🎯 **Aposte {sugestao}**  \nConfiança: {confianca}%"

# ==================== INÍCIO DO APP STREAMLIT ====================

st.set_page_config(page_title="Football Studio Analyzer", layout="centered")
st.title("🃏 Football Studio Analyzer")

# Inicialização do session_state DEPOIS das funções
if 'historico' not in st.session_state:
    st.session_state.historico = load_historico()

if 'entradas_hoje' not in st.session_state:
    st.session_state.entradas_hoje = 0

# ==================== INTERFACE ====================

st.subheader("➕ Adicionar rodada (texto rápido)")
input_rapido = st.text_input("Digite Home-Away (ex: K-Q, 9-J, Q-2):", placeholder="Ex: J-9")
if st.button("Adicionar via texto"):
    if input_rapido.strip():
        try:
            home, away = [x.strip().upper() for x in input_rapido.split('-')]
            if home in RANKS and away in RANKS:
                st.session_state.historico.append([home, away])
                save_historico(st.session_state.historico)
                winner = get_winner(home, away)
                st.success(f"Adicionado: {home}-{away} → **{winner} vence**")
            else:
                st.error("Rank inválido! Use apenas A,2-10,J,Q,K")
        except:
            st.error("Formato errado! Use exatamente 'Home-Away' como 'K-Q'")
    else:
        st.warning("Digite algo primeiro!")

st.divider()

st.subheader("➕ Adicionar rodada (manual)")
c1, c2 = st.columns(2)
with c1:
    home_manual = st.selectbox("Carta Home", RANKS, key="home_sel")
with c2:
    away_manual = st.selectbox("Carta Away", RANKS, key="away_sel")

if st.button("Adicionar manual"):
    st.session_state.historico.append([home_manual, away_manual])
    save_historico(st.session_state.historico)
    winner = get_winner(home_manual, away_manual)
    st.success(f"Adicionado: {home_manual}-{away_manual} → **{winner} vence**")

st.divider()

st.subheader("📊 Controle Diário")
st.write(f"Entradas usadas hoje: **{st.session_state.entradas_hoje} / 5**")
if st.button("🔄 Resetar contador diário"):
    st.session_state.entradas_hoje = 0
    st.success("Contador resetado!")

st.divider()

if st.button("🔍 Analisar e Sugerir Aposta", type="primary"):
    if st.session_state.entradas_hoje >= 5:
        st.warning("🚫 Limite diário de 5 entradas atingido!")
    else:
        resultado = sugestao_aposta(st.session_state.historico)
        st.markdown(f"### {resultado}")
        st.session_state.entradas_hoje += 1
        st.rerun()  # Atualiza o contador imediatamente

st.divider()

st.subheader("📜 Histórico Recente (últimas 10 rodadas)")
if st.session_state.historico:
    for rod in reversed(st.session_state.historico[-10:]):
        winner = get_winner(rod[0], rod[1])
        st.write(f"{rod[0]} - {rod[1]} → **{winner}**")
else:
    st.info("Nenhuma rodada adicionada ainda.")

# Botão para limpar tudo (opcional)
if st.button("🗑️ Limpar todo o histórico"):
    st.session_state.historico = []
    save_historico(st.session_state.historico)
    st.session_state.entradas_hoje = 0
    st.success("Histórico limpo!")
    st.rerun()
