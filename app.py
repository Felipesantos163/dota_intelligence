import streamlit as st
from simulator import DotaPredictor

# Configuração da Página
st.set_page_config(page_title="Dota 2 Predictor IA", page_icon="🧙‍♂️")

# Inicializa o preditor (usa cache para não carregar o modelo toda hora)
@st.cache_resource
def load_predictor():
    return DotaPredictor()

predictor = load_predictor()

st.title("🧙‍♂️ Dota 2 Draft Intelligence")
st.markdown("Preencha os dados abaixo para calcular as probabilidades de vitória.")

# --- SEÇÃO DE TIMES ---
st.subheader("🏢 Equipes")
col_t1, col_t2 = st.columns(2)
with col_t1:
    time_rad = st.text_input("Time Radiant (Nome ou ID)", placeholder="Ex: Team Liquid")
with col_t2:
    time_dire = st.text_input("Time Dire (Nome ou ID)", placeholder="Ex: Team Spirit")

# --- SEÇÃO DE DRAFT ---
st.subheader("⚔️ Draft dos Heróis")
col1, col2 = st.columns(2)

rad_h = []
dire_h = []

with col1:
    st.write("**RADIANT**")
    for i in range(5):
        rad_h.append(st.text_input(f"Slot {i+1}", key=f"r{i}"))

with col2:
    st.write("**DIRE**")
    for i in range(5):
        dire_h.append(st.text_input(f"Slot {i+1}", key=f"d{i}"))

# --- BOTÃO DE CÁLCULO ---
if st.button("📊 ANALISAR CONFRONTO", use_container_width=True):
    if any(h == "" for h in rad_h) or any(h == "" for h in dire_h):
        st.error("Por favor, preencha todos os 10 heróis.")
    else:
        with st.spinner("IA analisando padrões históricos..."):
            chance, erro = predictor.prever(rad_h, dire_h, time_rad, time_dire)
            
        if erro:
                st.info(f"📊 **Dados da IA:** Radiant (ID: {predictor.resolver_id_time(time_rad)}) vs Dire (ID: {predictor.resolver_id_time(time_dire)})")
        else:
                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Chance RADIANT", f"{chance*100:.2f}%")
                c2.metric("Chance DIRE", f"{(1-chance)*100:.2f}%")
                
                # Convertemos para float puro e garantimos que fique entre 0 e 1
                progresso_val = float(chance)
                progresso_val = max(0.0, min(1.0, progresso_val)) # Clamp entre 0 e 1
                
                st.progress(progresso_val)
                
                vencedor = "RADIANT" if chance > 0.5 else "DIRE"
                st.success(f"🔥 FAVORITO ESTATÍSTICO: **{vencedor}**")