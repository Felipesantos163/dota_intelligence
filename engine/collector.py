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

            # 1. Dados Básicos da Partida
            features = {
                'match_id': match_id,
                'radiant_win': 1 if data.get('radiant_win') else 0,
                'duration': data.get('duration'),
                'patch': data.get('patch'),
                'radiant_score': data.get('radiant_score', 0),
                'dire_score': data.get('dire_score', 0)
            }

            # 2. Listas para consolidar dados dos jogadores
            rad_stats = {'gpm': [], 'xpm': [], 'lh': [], 'dn': [], 'hd': [], 'td': [], 'heal': [], 'obs': [], 'sen': []}
            dire_stats = {'gpm': [], 'xpm': [], 'lh': [], 'dn': [], 'hd': [], 'td': [], 'heal': [], 'obs': [], 'sen': []}

            r_idx, d_idx = 1, 1
            for p in data['players']:
                side = 'r' if p.get('isRadiant') else 'd'
                idx = r_idx if p.get('isRadiant') else d_idx
                
                # Heróis do Draft
                features[f'{side}_hero_{idx}'] = p.get('hero_id')
                
                # Distribuição das estatísticas por time
                target_dict = rad_stats if p.get('isRadiant') else dire_stats
                
                # Usar "or 0" evita erros se o valor na API vier como None
                target_dict['gpm'].append(p.get('gold_per_min', 0) or 0)
                target_dict['xpm'].append(p.get('xp_per_min', 0) or 0)
                target_dict['lh'].append(p.get('last_hits', 0) or 0)
                target_dict['dn'].append(p.get('denies', 0) or 0)
                target_dict['hd'].append(p.get('hero_damage', 0) or 0)
                target_dict['td'].append(p.get('tower_damage', 0) or 0)
                target_dict['heal'].append(p.get('hero_healing', 0) or 0)
                target_dict['obs'].append(p.get('obs_placed', 0) or 0)
                target_dict['sen'].append(p.get('sen_placed', 0) or 0)

                if p.get('isRadiant'): r_idx += 1
                else: d_idx += 1

            # 3. Consolidação (Médias e Totais por Time)
            features.update({
                'rad_avg_gpm': sum(rad_stats['gpm']) / 5 if rad_stats['gpm'] else 0,
                'dire_avg_gpm': sum(dire_stats['gpm']) / 5 if dire_stats['gpm'] else 0,
                'rad_avg_xpm': sum(rad_stats['xpm']) / 5 if rad_stats['xpm'] else 0,
                'dire_avg_xpm': sum(dire_stats['xpm']) / 5 if dire_stats['xpm'] else 0,
                
                'rad_total_lh': sum(rad_stats['lh']),
                'dire_total_lh': sum(dire_stats['lh']),
                'rad_total_dn': sum(rad_stats['dn']),
                'dire_total_dn': sum(dire_stats['dn']),
                
                'rad_total_hero_dmg': sum(rad_stats['hd']),
                'dire_total_hero_dmg': sum(dire_stats['hd']),
                'rad_total_tower_dmg': sum(rad_stats['td']),
                'dire_total_tower_dmg': sum(dire_stats['td']),
                
                'rad_total_heal': sum(rad_stats['heal']),
                'dire_total_heal': sum(dire_stats['heal']),
                
                'rad_obs_placed': sum(rad_stats['obs']),
                'dire_obs_placed': sum(dire_stats['obs']),
                'rad_sen_placed': sum(rad_stats['sen']),
                'dire_sen_placed': sum(dire_stats['sen'])
            })

            # 4. Objetivos e Timings
            features.update({
                'kills_10m': sum(1 for k in data.get('kills_log', []) if k['time'] <= 600),
                'first_blood_time': data.get('first_blood_time', 0),
                'first_blood_team': -1, # 0 = Radiant, 1 = Dire
                'first_tower_team': -1, # 0 = Radiant, 1 = Dire
                'first_roshan_time': 0,
                'first_roshan_team': -1 # 0 = Radiant, 1 = Dire
            })

            if data.get('objectives'):
                for obj in data['objectives']:
                    if obj['type'] == 'CHAT_MESSAGE_FIRSTBLOOD' and features['first_blood_team'] == -1:
                        features['first_blood_team'] = 0 if obj.get('player_slot', 0) < 128 else 1
                    
                    
                    if obj['type'] == 'CHAT_MESSAGE_TOWER_KILL' and features['first_tower_team'] == -1:
                        features['first_tower_team'] = 0 if obj.get('team') == 2 else 1
                    elif obj['type'] == 'BUILDING_KILL' and 'tower' in obj.get('key', '') and features['first_tower_team'] == -1:
                        if 'goodguys' in obj.get('key', ''): features['first_tower_team'] = 1 
                        elif 'badguys' in obj.get('key', ''): features['first_tower_team'] = 0
                    
                    if obj['type'] == 'CHAT_MESSAGE_ROSHAN_KILL' and features['first_roshan_team'] == -1:
                        features['first_roshan_time'] = obj['time']
                        features['first_roshan_team'] = 0 if obj.get('player_slot', 0) < 128 else 1

            # 5. Dinâmica de Ouro e Viradas
            gold_adv = data.get('radiant_gold_adv', [])
            if gold_adv:
                features['max_gold_swing'] = max(abs(x) for x in gold_adv)
                features['mudancas_lideranca'] = sum(1 for i in range(1, len(gold_adv)) if (gold_adv[i-1] > 0 and gold_adv[i] < 0) or (gold_adv[i-1] < 0 and gold_adv[i] > 0))
                
                # Cálculo da maior virada
                maior_desvantagem = min(gold_adv) if features['radiant_win'] == 1 else max(gold_adv)
                features['maior_virada_ouro'] = abs(maior_desvantagem) if (features['radiant_win'] == 1 and maior_desvantagem < 0) or (features['radiant_win'] == 0 and maior_desvantagem > 0) else 0
                
                # Volatilidade (Soma das variações)
                features['volatilidade_jogo'] = sum(abs(gold_adv[i] - gold_adv[i-1]) for i in range(1, len(gold_adv)))
            else:
                features.update({
                    'max_gold_swing': 0,
                    'mudancas_lideranca': 0,
                    'maior_virada_ouro': 0,
                    'volatilidade_jogo': 0
                })

            return features

        except Exception as e:
            print(f"\n⚠️ Erro ao processar ID {match_id}: {e}")
            return None