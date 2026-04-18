import streamlit as st
from simulator import DotaPredictor

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dota 2 Intelligence IA", page_icon="🧙‍♂️", layout="wide")

# 2. CARREGAMENTO DO MODELO (Cache para performance)
@st.cache_resource
def load_predictor():
    return DotaPredictor()

# 3. DICIONÁRIO OFFLINE COMPLETO (Baseado na tabela oficial enviada)
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

# Inicialização de dados
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

# 1. Cria a lista de opções ordenada alfabeticamente (com um espaço em branco no início)
opcoes_herois = [""] + sorted(list(dict_herois.keys()))

# 2. Inicializa a "memória" do Streamlit para os slots (necessário para o botão inverter funcionar)
for i in range(5):
    if f"r{i}" not in st.session_state: st.session_state[f"r{i}"] = ""
    if f"d{i}" not in st.session_state: st.session_state[f"d{i}"] = ""

# 3. Botão para inverter os drafts
if st.button("🔄 Inverter Lados"):
    for i in range(5):
        # Troca os valores da memória cruzando Radiant com Dire
        st.session_state[f"r{i}"], st.session_state[f"d{i}"] = st.session_state[f"d{i}"], st.session_state[f"r{i}"]

col_rad_ui, col_dire_ui = st.columns(2)

rad_h_input = []
dire_h_input = []

with col_rad_ui:
    st.markdown("<h4 style='color: #4CAF50;'>🟢 RADIANT</h4>", unsafe_allow_html=True)
    for i in range(5):
        # Trocado text_input por selectbox
        rad_h_input.append(st.selectbox(f"Slot {i+1}", options=opcoes_herois, key=f"r{i}"))

with col_dire_ui:
    st.markdown("<h4 style='color: #F44336;'>🔴 DIRE</h4>", unsafe_allow_html=True)
    for i in range(5):
        # Trocado text_input por selectbox
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
            erros.append(f"Herói '{valor}' no Slot {idx+1} ({nome_lado}) não reconhecido.")
    return ids_finais, erros

# --- BOTÃO DE ANÁLISE ---
st.write("")
if st.button("📊 ANALISAR CONFRONTO", use_container_width=True):
    rad_h_ids, erros_rad = validar_e_converter(rad_h_input, "Radiant")
    dire_h_ids, erros_dire = validar_e_converter(dire_h_input, "Dire")
    
    total_erros = erros_rad + erros_dire
    
    if total_erros:
        st.error("⚠️ Problemas encontrados no preenchimento:")
        for e in total_erros:
            st.warning(e)
    else:
        with st.spinner("IA analisando padrões históricos..."):
            # 1. Probabilidade Real (Draft + Time)
            chance_total, erro_ia = predictor.prever(rad_h_ids, dire_h_ids, time_rad, time_dire)
            # 2. Probabilidade Pura (Somente Draft - ignorando times)
            chance_draft, _ = predictor.prever(rad_h_ids, dire_h_ids, None, None)

        if erro_ia:
            st.error(f"Erro na IA: {erro_ia}")
        else:
            st.divider()
            
            # Exibe IDs para conferência
            id_rad_res = predictor.resolver_id_time(time_rad) if time_rad else "Neutro"
            id_dire_res = predictor.resolver_id_time(time_dire) if time_dire else "Neutro"
            st.info(f"📊 **Dados Processados:** Radiant (ID: {id_rad_res}) vs Dire (ID: {id_dire_res})")

            res_col1, res_col2 = st.columns(2)

            # Lógica de exibição: Apenas Draft
            with res_col1:
                st.markdown("### 🎯 Apenas Draft")
                st.caption("Considera sinergias de heróis e counters (Ignora o time).")
                st.metric("Vantagem Radiant", f"{chance_draft*100:.2f}%")
                st.progress(max(0.0, min(1.0, float(chance_draft))))

            # Lógica de exibição: Draft + Time
            with res_col2:
                st.markdown("### 🏢 Draft + Time")
                st.caption("Considera o draft somado ao histórico do time/organização.")
                impacto = (chance_total - chance_draft) * 100
                st.metric("Vantagem Radiant", f"{chance_total*100:.2f}%", delta=f"{impacto:+.2f}% vs Draft")
                st.progress(max(0.0, min(1.0, float(chance_total))))

            # Veredito Final
            vencedor = "RADIANT" if chance_total > 0.5 else "DIRE"
            cor = "success" if (vencedor == "RADIANT" and chance_total > 0.55) or (vencedor == "DIRE" and chance_total < 0.45) else "info"
            
            st.write("")
            if cor == "success":
                st.success(f"🔥 FAVORITO ESTATÍSTICO: **{vencedor}**")
            else:
                st.info(f"⚖️ CONFRONTO EQUILIBRADO: Favoritismo leve para **{vencedor}**")