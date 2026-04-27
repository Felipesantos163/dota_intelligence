import joblib
import pandas as pd
import os

class DotaPredictor:
    def __init__(self):
        self.stats_path = 'models/win_rates.pkl'
        self.team_stats = joblib.load(self.stats_path) if os.path.exists(self.stats_path) else {}

        # Carrega todos os modelos e suas respectivas tabelas de confiabilidade
        self.modelos = {
            'win': self._carregar('models/draft_intelligence_v2.pkl', 'models/model_columns.pkl', 'models/draft_intelligence_v2_conf.pkl'),
            'fb': self._carregar('models/first_blood_v1.pkl', 'models/fb_columns.pkl', 'models/first_blood_v1_conf.pkl'),
            'tower': self._carregar('models/first_tower_v1.pkl', 'models/ft_columns.pkl', 'models/first_tower_v1_conf.pkl')
        }

    def _carregar(self, mod_path, col_path, conf_path):
        if os.path.exists(mod_path) and os.path.exists(col_path):
            return {
                'modelo': joblib.load(mod_path),
                'cols': joblib.load(col_path),
                'conf': joblib.load(conf_path) if os.path.exists(conf_path) else {}
            }
        return None

    def resolver_id_time(self, entrada):
        """Converte Nome ou ID para evitar falhas"""
        if not entrada or str(entrada).strip() == "": return None
        if str(entrada).strip().isdigit():
            final_id = int(str(entrada).strip())
            # Confere se o ID do time existe no modelo principal
            if self.modelos['win'] and (f"radiant_team_id_{final_id}" in self.modelos['win']['cols'] or f"dire_team_id_{final_id}" in self.modelos['win']['cols']):
                return final_id
        return None

    def _obter_confiabilidade(self, prob, tabela_conf):
        """Busca a precisão histórica da faixa de probabilidade"""
        if not tabela_conf: return "N/A"
        for faixa, real_rate in tabela_conf.items():
            if prob in faixa:
                if pd.isna(real_rate): return "Sem dados suficientes na faixa"
                return f"{real_rate*100:.1f}%"
        return "N/A"

    def prever(self, rad_heroes, dire_heroes, team_rad_nome=None, team_dire_nome=None):
        if not self.modelos['win']:
            return None, "❌ Erro: Modelo principal (Vitória) não treinado."

        team_rad_id = self.resolver_id_time(team_rad_nome)
        team_dire_id = self.resolver_id_time(team_dire_nome)

        resultados = {}

        # Executa a previsão para cada evento (Vitória, FB, Torre)
        for chave, config in self.modelos.items():
            if not config: continue
            
            input_data = {}
            input_data['rad_team_wr'] = self.team_stats.get(team_rad_id, 0.5)
            input_data['dire_team_wr'] = self.team_stats.get(team_dire_id, 0.5)
            
            if team_rad_id: input_data[f'radiant_team_id_{team_rad_id}'] = 1
            if team_dire_id: input_data[f'dire_team_id_{team_dire_id}'] = 1
                
            # MÉTODO SIMÉTRICO DE HERÓIS (+1/-1)
            for h_id in rad_heroes:
                col_name = f'hero_{int(h_id)}_adv'
                if col_name in config['cols']: input_data[col_name] = 1
                    
            for h_id in dire_heroes:
                col_name = f'hero_{int(h_id)}_adv'
                if col_name in config['cols']: input_data[col_name] = -1

            # Monta matriz
            df_predict = pd.DataFrame(columns=config['cols'])
            df_predict.loc[0] = 0 
            
            for col, valor in input_data.items():
                if col in df_predict.columns:
                    df_predict.loc[0, col] = valor
            
            df_predict = df_predict[config['cols']]
            
            # Predição e Confiabilidade
            prob_radiant = config['modelo'].predict_proba(df_predict)[0][1]
            conf_text = self._obter_confiabilidade(prob_radiant, config['conf'])
            
            resultados[chave] = {
                'prob_radiant': prob_radiant,
                'prob_dire': 1 - prob_radiant,
                'favorito': 'RADIANT' if prob_radiant > 0.5 else 'DIRE',
                'confiabilidade': conf_text
            }

        return resultados, None

# ==========================================
# MENU INTERATIVO PARA TESTES NO TERMINAL
# ==========================================
def menu_interativo():
    predictor = DotaPredictor()
    
    print("\n" + "═"*50)
    print("      🧙‍♂️ SIMULADOR DOTA IA (MODO TERMINAL) 🧙‍♂️")
    print("═"*50)

    t_rad = input("\nID do Time Radiant (Deixe em branco para Neutro): ")
    t_dire = input("ID do Time Dire (Deixe em branco para Neutro):    ")

    print("\n--- DRAFT RADIANT (Digite apenas IDs numéricos, ex: 14) ---")
    r_h = [input(f"Slot {i+1} ID: ") for i in range(5)]

    print("\n--- DRAFT DIRE (Digite apenas IDs numéricos, ex: 120) ---")
    d_h = [input(f"Slot {i+1} ID: ") for i in range(5)]

    print("\n🧠 Analisando padrões históricos...")
    resultados, erro = predictor.prever(r_h, d_h, t_rad, t_dire)

    if erro:
        print(f"❌ Erro na simulação: {erro}")
    else:
        print("\n" + "█"*50)
        win = resultados.get('win')
        if win:
            print(f"🏆 PREVISÃO DE VITÓRIA:")
            print(f"  RADIANT: {win['prob_radiant']*100:.2f}% | DIRE: {win['prob_dire']*100:.2f}%")
            print(f"  🎯 CONFIABILIDADE (Taxa de Acerto): {win['confiabilidade']}")
            print("-" * 50)
            
        fb = resultados.get('fb')
        if fb:
            print(f"🩸 FIRST BLOOD:  {fb['favorito']} ({max(fb['prob_radiant'], fb['prob_dire'])*100:.1f}%) | Confiança: {fb['confiabilidade']}")
            
        tw = resultados.get('tower')
        if tw:
            print(f"🗼 PRIMEIRA TORRE: {tw['favorito']} ({max(tw['prob_radiant'], tw['prob_dire'])*100:.1f}%) | Confiança: {tw['confiabilidade']}")
        print("█"*50)

if __name__ == "__main__":
    while True:
        menu_interativo()
        if input("\nDeseja realizar outro teste? (s/n): ").lower() != 's':
            print("\nEncerrando simulador. GG WP!")
            break