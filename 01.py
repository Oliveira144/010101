import streamlit as st
import json
import collections
import math

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="Football Studio Analyzer", layout="centered")

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {r: i + 1 for i, r in enumerate(RANKS)}
HIST_FILE = 'historico_fs.json'

# =====================
# PERSISTÊNCIA
# =====================
def load_historico():
    try:
        with open(HIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_historico(historico):
    with open(HIST_FILE, 'w') as f:
        json.dump(historico, f)

# =====================
# LÓGICA (INALTERADA)
# =====================
def add_rodada(historico, input_str):
    home, away = input_str.upper().split('-')
    if home not in RANKS or away not in RANKS:
        raise ValueError("Rank inválido!")
    historico.append([home, away])
    save_historico(historico)

def get_winner(home, away):
    h_val = RANK_VALUES[home]
    a_val = RANK_VALUES[away]
    if h_val > a_val:
        return 'Home'
    elif h_val < a_val:
        return 'Away'
    else:
        return 'Tie'

def analise_frequencias(historico):
    home_ranks = [h for h, _ in historico]
    away_ranks = [a for _, a in historico]
    return {
        'home': dict(collections.Counter(home_ranks)),
        'away': dict(collections.Counter(away_ranks))
    }

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

def detect_repeticoes(historico, n=2):
    reps = []
    for i in range(len(historico) - n + 1):
        seq = historico[i:i+n]
        if all(s == seq[0] for s in seq[1:]):
            reps.append(seq)
    return reps

def detect_inversoes(historico):
    invs = []
    for i in range(1, len(historico)):
        prev_h, prev_a = historico[i-1]
        curr_h, curr_a = historico[i]
        if prev_h == curr_a and prev_a == curr_h:
            invs.append((historico[i-1], historico[i]))
    return invs

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
    return {k: v / total for k, v in transitions[last].items()}

def sugestao_aposta(historico):
    if len(historico) < 5:
        return "Histórico pequeno demais. Adicione mais rodadas."
    
    streaks = detect_streaks(historico)
    probs = markov_prob(historico)
    invs = detect_inversoes(historico)
    
    sugestao = None
    confianca = 0

    if streaks and streaks[-1][1] >= 3:
        last = streaks[-1][0]
        sugestao = 'Away' if last == 'Home' else 'Home'
        confianca = 70 + (streaks[-1][1] - 3) * 5

    elif invs and len(invs) > 1:
        sugestao = 'Tie' if get_winner(*historico[-1]) == 'Tie' else 'Inversão esperada'
        confianca = 65

    elif probs:
        sugestao = max(probs, key=probs.get)
        confianca = int(probs[sugestao] * 100)

    confianca = min(confianca, int(math.sqrt(len(historico)) * 10))

    if confianca < 60:
        return "Sem padrão forte detectado. Espere."
    return f"Aposte {sugestao} ({confianca}% confiança)"

# =====================
# STREAMLIT APP
# =====================
st.title("🎴 Football Studio Analyzer")

if "historico" not in st.session_state:
    st.session_state.historico = load_historico()

entrada = st.text_input("Adicionar rodada (ex: K-Q, 10-A):")

if st.button("Adicionar"):
    try:
        add_rodada(st.session_state.historico, entrada)
        st.success("Rodada adicionada!")
    except Exception as e:
        st.error(str(e))

st.subheader("📊 Histórico")
st.write(st.session_state.historico)

st.subheader("📈 Análises")
st.write("Frequências:", analise_frequencias(st.session_state.historico))
st.write("Streaks:", detect_streaks(st.session_state.historico))
st.write("Repetições:", detect_repeticoes(st.session_state.historico))
st.write("Inversões:", detect_inversoes(st.session_state.historico))
st.write("Markov:", markov_prob(st.session_state.historico))

st.subheader("🎯 Sugestão")
st.info(sugestao_aposta(st.session_state.historico))
