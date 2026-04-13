import requests
import time

class DotaCollector:
    def __init__(self):
        self.base_url = "https://api.opendota.com/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def process_match_deep(self, match_id):
        url = f"{self.base_url}/matches/{match_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200: return None
            data = response.json()
            
            if not data.get('players'): return None

            # 1. Dados Básicos e Draft
            features = {
                'match_id': match_id,
                'radiant_win': 1 if data['radiant_win'] else 0,
                'duration': data.get('duration'),
                'first_blood_time': data.get('first_blood_time', 0),
                'patch': data.get('patch')
            }

            # Mapeamento de Heróis (r_hero_1..5 e d_hero_1..5)
            r_idx, d_idx = 1, 1
            for p in data['players']:
                side = 'r' if p['isRadiant'] else 'd'
                idx = r_idx if p['isRadiant'] else d_idx
                features[f'{side}_hero_{idx}'] = p['hero_id']
                if p['isRadiant']: r_idx += 1
                else: d_idx += 1

            # 2. Performance Econômica
            rad_gpm = [p.get('gold_per_min', 0) for p in data['players'] if p['isRadiant']]
            dire_gpm = [p.get('gold_per_min', 0) for p in data['players'] if not p['isRadiant']]
            features['rad_avg_gpm'] = sum(rad_gpm) / 5 if rad_gpm else 0
            features['dire_avg_gpm'] = sum(dire_gpm) / 5 if dire_gpm else 0

            # 3. Objetivos (Roshan, Tormentor e Kills)
            features.update({
                'kills_10m': 0,
                'first_roshan_time': 0,
                'first_roshan_team': -1, # -1: nenhum, 0: radiant, 1: dire
                'max_gold_swing': 0
            })

            # Contagem de Kills aos 10 minutos (600s)
            if data.get('kills_log'):
                features['kills_10m'] = sum(1 for k in data['kills_log'] if k['time'] <= 600)

            # Primeiro Roshan
            if data.get('objectives'):
                for obj in data['objectives']:
                    if obj['type'] == 'CHAT_MESSAGE_ROSHAN_KILL':
                        features['first_roshan_time'] = obj['time']
                        # player_slot < 128 é Radiant
                        features['first_roshan_team'] = 0 if obj.get('player_slot', 0) < 128 else 1
                        break # Pega apenas o primeiro

            # Balanço de Ouro (Gold Swing)
            if data.get('radiant_gold_adv'):
                features['max_gold_swing'] = max([abs(x) for x in data['radiant_gold_adv']])

            return features
        except Exception as e:
            print(f"\n⚠️ Erro ao processar ID {match_id}: {e}")
            return None