import streamlit as st
from simulator import DotaPredictor

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dota 2 Intelligence IA", page_icon="🧙‍♂️", layout="wide")

# 2. CARREGAMENTO DO MODELO (Cache para performance)
@st.cache_resource
def load_predictor():
    return DotaPredictor()

# 3. DICIONÁRIO OFFLINE COMPLETO
@st.cache_data
def carregar_dicionario_herois():
    return {
        "anti-mage": 1, "axe": 2, "bane": 3, "bloodseeker": 4, "crystal maiden": 5, "drow ranger": 6, 
        "earthshaker": 7, "juggernaut": 8, "mirana": 9, "morphling": 10, "shadow fiend": 11, "sf": 11, 
        "phantom lancer": 12, "puck": 13, "pudge": 14, "razor": 15, "sand king": 16, "storm spirit": 17, 
        "sven": 18, "tiny": 19, "vengeful spirit": 20, "windranger": 21, "zeus": 22, "kunkka": 23, 
        "lina": 25, "lion": 26, "shadow shaman": 27, "slardar": 28, "tidehunter": 29, "witch doctor": 30, 
        "lich": 31, "riki": 32, "enigma": 33, "tinker": 34, "sniper": 35, "necrophos": 36, "warlock": 37, 
        "beastmaster": 38, "queen of pain": 39, "venomancer": 40, "faceless void": 41, "wraith king": 42, 
        "death prophet": 43, "phantom assassin": 44, "pa": 44, "pugna": 45, "templar assassin": 46, 
        "viper": 47, "luna": 48, "dragon knight": 49, "dazzle": 50, "clockwerk": 51, "leshrac": 52, 
        "nature's prophet": 53, "np": 53, "lifestealer": 54, "dark seer": 55, "clinkz": 56, "omniknight": 57, 
        "enchantress": 58, "huskar": 59, "night stalker": 60, "broodmother": 61, "bounty hunter": 62, 
        "weaver": 63, "jakiro": 64, "batrider": 65, "chen": 66, "spectre": 67, "ancient apparition": 68, 
        "doom": 69, "ursa": 70, "spirit breaker": 71, "gyrocopter": 72, "alchemist": 73, "invoker": 74, 
        "silencer": 75, "outworld destroyer": 76, "od": 76, "lycan": 77, "brewmaster": 78, "shadow demon": 79, 
        "lone druid": 80, "chaos knight": 81, "meepo": 82, "treant protector": 83, "ogre magi": 84, 
        "undying": 85, "rubick": 86, "disruptor": 87, "nyx assassin": 88, "naga siren": 89, 
        "keeper of the light": 90, "kotl": 90, "io": 91, "visage": 92, "slark": 93, "medusa": 94, 
        "troll warlord": 95, "centaur warrunner": 96, "magnus": 97, "timbersaw": 98, "bristleback": 99, 
        "tusk": 100, "skywrath mage": 101, "abaddon": 102, "elder titan": 103, "legion commander": 104, 
        "techies": 105, "ember spirit": 106, "earth spirit": 107, "underlord": 108, "terrorblade": 109, 
        "phoenix": 110, "oracle": 111, "winter wyvern": 112, "arc warden": 113, "monkey king": 114, 
        "dark willow": 119, "pangolier": 120, "grimstroke": 121, "hoodwink": 123, "void spirit": 126, 
        "snapfire": 128, "mars": 129, "ringmaster": 131, "dawnbreaker": 135, "marci": 136, 
        "primal beast": 137, "muerta": 138, "kez": 145, "largo": 155
    }

predictor = load_predictor()
dict_herois = carregar_dicionario_herois()

# --- INTERFACE ---
st.title("🧙‍♂️ Dota 2 Draft Intelligence")
st.sidebar.success(f"✅ Sistema Local Ativo ({len(set(dict_herois.values()))} heróis únicos)")
st.markdown("Preencha os times e os heróis (Nome ou ID) para analisar o confronto.")

# --- SEÇÃO DE TIMES ---
st.subheader("🏢 Equipes")
col_t1, col_t2 = st.columns(2)
with col_t1:
    time_rad = st.text_input("Time Radiant (ID numérico)", placeholder="Ex: 1838315")
with col_t2:
    time_dire = st.text_input("Time Dire (ID numérico)", placeholder="Ex: 7373486")

st.divider()

# --- SEÇÃO DE DRAFT ---
st.subheader("⚔️ Draft dos Heróis")
st.caption("Selecione os heróis na lista (você pode digitar para buscar rapidamente).")

opcoes_herois = [""] + sorted(list(dict_herois.keys()))

for i in range(5):
    if f"r{i}" not in st.session_state: st.session_state[f"r{i}"] = ""
    if f"d{i}" not in st.session_state: st.session_state[f"d{i}"] = ""

if st.button("🔄 Inverter Lados"):
    for i in range(5):
        st.session_state[f"r{i}"], st.session_state[f"d{i}"] = st.session_state[f"d{i}"], st.session_state[f"r{i}"]

col_rad_ui, col_dire_ui = st.columns(2)
rad_h_input = []
dire_h_input = []

with col_rad_ui:
    st.markdown("<h4 style='color: #4CAF50;'>🟢 RADIANT</h4>", unsafe_allow_html=True)
    for i in range(5):
        rad_h_input.append(st.selectbox(f"Slot {i+1}", options=opcoes_herois, key=f"r{i}"))

with col_dire_ui:
    st.markdown("<h4 style='color: #F44336;'>🔴 DIRE</h4>", unsafe_allow_html=True)
    for i in range(5):
        dire_h_input.append(st.selectbox(f"Slot {i+1}", options=opcoes_herois, key=f"d{i}"))

# --- LÓGICA DE CONVERSÃO ---
def validar_e_converter(lista_inputs, nome_lado):
    ids_finais = []
    erros = []
    for idx, valor in enumerate(lista_inputs):
        v = valor.strip().lower()
        if not v:
            erros.append(f"O Slot {idx+1} ({nome_lado}) está vazio.")
            continue
        if v.isdigit():
            ids_finais.append(int(v))
        elif v in dict_herois:
            ids_finais.append(dict_herois[v])
        else:
            erros.append(f"Herói '{valor}' não reconhecido.")
    return ids_finais, erros

# --- BOTÃO DE ANÁLISE ---
st.write("")
if st.button("📊 ANALISAR CONFRONTO", use_container_width=True):
    rad_h_ids, erros_rad = validar_e_converter(rad_h_input, "Radiant")
    dire_h_ids, erros_dire = validar_e_converter(dire_h_input, "Dire")
    total_erros = erros_rad + erros_dire
    
    if total_erros:
        st.error("⚠️ Problemas encontrados no preenchimento:")
        for e in total_erros: st.warning(e)
    else:
        with st.spinner("IA analisando previsões e níveis de confiança..."):
            resultados, erro_ia = predictor.prever(rad_h_ids, dire_h_ids, time_rad, time_dire)

        if erro_ia:
            st.error(erro_ia)
        else:
            st.divider()
            
            # --- PAINEL PRINCIPAL: VITÓRIA ---
            st.subheader("🏆 Previsão de Vitória")
            res_win = resultados.get('win')
            if res_win:
                vencedor = res_win['favorito']
                chance = max(res_win['prob_radiant'], res_win['prob_dire'])
                
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    st.metric("Time Favorito", vencedor, f"{chance*100:.1f}% de probabilidade")
                    st.progress(float(res_win['prob_radiant']))
                with col_w2:
                    st.metric("🎯 Taxa de Acerto Real (Confiabilidade)", res_win['confiabilidade'])
                    st.caption("Precisão histórica do modelo para probabilidades nesta faixa.")

            st.divider()
            
            # --- PAINEL SECUNDÁRIO: OBJETIVOS ---
            st.subheader("🎯 Objetivos Antecipados")
            col_fb, col_tw = st.columns(2)
            
            with col_fb:
                st.markdown("### 🩸 First Blood")
                res_fb = resultados.get('fb')
                if res_fb:
                    chance_fb = max(res_fb['prob_radiant'], res_fb['prob_dire'])
                    st.metric(res_fb['favorito'], f"{chance_fb*100:.1f}% de chance")
                    st.caption(f"**Confiabilidade:** {res_fb['confiabilidade']}")
                else:
                    st.warning("Modelo de First Blood ausente.")
                    
            with col_tw:
                st.markdown("### 🗼 Primeira Torre")
                res_tw = resultados.get('tower')
                if res_tw:
                    chance_tw = max(res_tw['prob_radiant'], res_tw['prob_dire'])
                    st.metric(res_tw['favorito'], f"{chance_tw*100:.1f}% de chance")
                    st.caption(f"**Confiabilidade:** {res_tw['confiabilidade']}")
                else:
                    st.info("Pendente: Aguardando mais dados da mineração.")