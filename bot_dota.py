import os
import time
import requests
import re
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from simulator import DotaPredictor 
from live_tracker import DotaLiveTracker

load_dotenv()

# --- 1. CONFIGURAÇÃO DO ALVO ---
MAPA_ALVO = "Game 1 Winner"

# 🎯 COLE A URL DA PÁGINA DO JOGO AQUI:
LINK_DO_EVENTO = "https://polymarket.com/esports/dota-2/1win-essence/dota2-z10-l1ga-2026-05-02"

dict_times = {
    "team falcons": 8599101, "falcons": 8599101,
    "tundra esports": 8291895, "tundra": 8291895,
    "team liquid": 2163, "liquid": 2163,
    "team spirit": 7119388, "spirit": 7119388,
    "xtreme gaming": 8598463, "xtreme": 8598463,
    "betboom team": 8599364, "betboom": 8599364,
    "gaimin gladiators": 8598687, "gaimin": 8598687, "gg": 8598687,
    "parivision": 8806552, "pari": 8806552,
    "aurora gaming": 8605863, "aurora": 8605863,
    "mouz": 8887163, 
    "heroic": 8945763,
    "natus vincere": 36, "navi": 36, "na'vi": 36,
    "virtus.pro": 188390, "vp": 188390,
    "og": 2586976,
    "cheeki breeki": 10108713,
    "l1ga team": 9303383, "l1ga": 9303383,
    "south america rejects": 10108947, "sar": 10108947, "sar1": 10108947,
    "team lynx": 9928636, "lynx": 9928636,
    "inner circle": 10019843, "insanity": 10019843,
    "rune eaters": 9895247, "rune": 9895247,
    "power rangers": 55, "powerrangers": 55,
    "zero tenacity": 9600141, "z10": 9600141,
    "nigma galaxy": 7554697, "nigma": 7554697,
    "1win": 9239858,
    "roar gaming": 9308871, "roar": 9308871,
    "yakult brothers": 9351740, "yakult": 9351740,
    "mideng dreamer": 9314482, "mideng": 9314482,
    "vici gaming": 726228, "vg": 726228,
    "cloud dawning": 9318855, "cloud": 9318855,
}

# --- 2. FUNÇÕES AUXILIARES ---
def executar_aposta_simulada(tokens, time_escolhido, lado_aposta, confianca):
    token_alvo = tokens[0] if lado_aposta == "YES" else tokens[1]
    
    print(f"\n--- 💸 ESTRATÉGIA DE EXECUÇÃO ---")
    print(f"🎯 Alvo: {time_escolhido['nome']} (Apostando em: {lado_aposta})")
    print(f"🔑 ID do Token: {token_alvo}")
    print(f"📊 Confiança IA: {confianca*100:.2f}%")
    print(f"💰 Valor Planejado: 5.0 USDC")
    print(f"🚫 [MODO SIMULAÇÃO] Ordem pronta para disparo.")
    print(f"--------------------------------\n")

# --- 3. ROBÔ PRINCIPAL ---
def iniciar_robo():
    print("🤖 Iniciando Dota Intelligence Bot (Modo Sniper URL)...")
    
    predictor = DotaPredictor()
    url_eventos = "https://gamma-api.polymarket.com/events"
    
    # Extrai o slug automaticamente do link
    slug_alvo = LINK_DO_EVENTO.split('/')[-1].split('?')[0]
    
    print(f"📡 Acedendo diretamente ao alvo: {slug_alvo}")
    
    try:
        res = requests.get(url_eventos, params={"slug": slug_alvo})
        dados = res.json()
        if not dados:
            print("❌ Evento não encontrado. Verifique se o link está correto.")
            return
            
        evento = dados[0] if isinstance(dados, list) else dados
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return

    titulo_evento = evento.get('title', '').lower()
    
    # Extrai os times para obter os IDs do Tracker
    times_no_jogo = []
    for nome, t_id in dict_times.items():
        if re.search(r'\b' + re.escape(nome.lower()) + r'\b', titulo_evento):
            if not any(t['id'] == t_id for t in times_no_jogo):
                times_no_jogo.append({'nome': nome.title(), 'id': t_id})
            
    if len(times_no_jogo) >= 2:
        time_a, time_b = times_no_jogo[0], times_no_jogo[1]
        print(f"✅ Equipas identificadas: {time_a['nome']} vs {time_b['nome']}")
        
        encontrou_mercado = False
        for m in evento.get('markets', []):
            pergunta = m.get('question', '').lower()
            ativo = m.get('active')
            fechado = m.get('closed')
            
            if MAPA_ALVO.lower() in pergunta and ativo and not fechado:
                print(f"🎯 MERCADO TRAVADO: {MAPA_ALVO}")
                encontrou_mercado = True
                
                tracker = DotaLiveTracker()
                # O timeout está em 10 min para dar tempo de apanhar o draft
                id_rad, id_dire, rad_h, dire_h = tracker.buscar_draft(time_a['id'], time_b['id'], timeout_minutos=10)
                
                if rad_h and dire_h:
                    print(f"🧬 Radiant: {rad_h} | Dire: {dire_h}")
                    winrate, _ = predictor.prever(rad_h, dire_h, id_rad, id_dire)
                    print(f"📊 Winrate IA: {winrate*100:.2f}%")

                    tokens = m.get('clobTokenIds', ["ERRO", "ERRO"])
                    if winrate > 0.60:
                        executar_aposta_simulada(tokens, time_a, "YES", winrate)
                    elif (1 - winrate) > 0.60:
                        executar_aposta_simulada(tokens, time_b, "NO", (1 - winrate))
                    else:
                        print("⚖️ Equilibrado. Sem entrada.")
                break 
                
        if not encontrou_mercado:
            print(f"⚠️ O mercado '{MAPA_ALVO}' já fechou ou não existe neste evento.")
    else:
        print("❌ Não foi possível identificar as duas equipas no título do evento. Confirme o dict_times.")

if __name__ == "__main__":
    iniciar_robo()