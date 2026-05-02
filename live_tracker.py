import requests
import time

class DotaLiveTracker:
    def __init__(self):
        self.base_url = "https://api.opendota.com/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def buscar_draft(self, id_time_a, id_time_b, timeout_minutos=15):
        print(f"👀 Rastreando dados ao vivo na OpenDota para {id_time_a} vs {id_time_b}...")
        tempo_inicio = time.time()
        
        while (time.time() - tempo_inicio) < (timeout_minutos * 60):
            try:
                res = requests.get(f"{self.base_url}/live", headers=self.headers, timeout=10)
                
                if res.status_code == 200:
                    partidas_live = res.json()
                    
                    for p in partidas_live:
                        # Extrai os IDs das equipas
                        rad_id = p.get('team_id_radiant') or p.get('radiant_team_id')
                        dire_id = p.get('team_id_dire') or p.get('dire_team_id')
                        match_id = p.get('match_id')
                        
                        if (rad_id == id_time_a and dire_id == id_time_b) or \
                           (rad_id == id_time_b and dire_id == id_time_a):
                            
                            jogadores = p.get('players', [])
                            radiant_heroes = []
                            dire_heroes = []
                            
                            # Varre os 10 jogadores do lobby
                            for j in jogadores:
                                h_id = j.get('hero_id', 0)
                                if h_id > 0:
                                    # 'team' 0 é o lado Radiant, 'team' 1 é o lado Dire
                                    if j.get('team') == 0:
                                        radiant_heroes.append(h_id)
                                    elif j.get('team') == 1:
                                        dire_heroes.append(h_id)

                            count_rad = len(radiant_heroes)
                            count_dire = len(dire_heroes)
                            
                            if count_rad == 5 and count_dire == 5:
                                print(f"\n✅ Draft 100% concluído! (Match ID: {match_id})")
                                return rad_id, dire_id, radiant_heroes, dire_heroes
                            else:
                                # Isto mostra exatamente quantos heróis a API já conseguiu ler
                                print(f"⏳ Jogo {match_id} na rede. Aguardando picks (Delay DotaTV). Radiant: {count_rad}/5 | Dire: {count_dire}/5", end="\r")
                            
                            break # Achou o jogo, pode parar de procurar nos outros lobbies
                            
                elif res.status_code == 429:
                    print("⚠️ Limite da OpenDota atingido! Aguardando...", end="\r")
                else:
                    print(f"⚠️ Erro HTTP: {res.status_code}", end="\r")
                            
            except Exception as e:
                print(f"⚠️ Erro de rede: {e}", end="\r")
            
            # Pausa de 10 segundos para não ser banido pela OpenDota
            time.sleep(10)
            
        print("\n❌ Timeout: O jogo não revelou o draft completo a tempo.")
        return None, None, None, None