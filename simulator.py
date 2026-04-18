import joblib
import pandas as pd
import os

class DotaPredictor:
    def __init__(self):
        # 1. Caminhos atualizados para os arquivos gerados pelo trainer V2
        self.model_path = 'models/draft_intelligence_v2.pkl'
        self.cols_path = 'models/model_columns.pkl'
        self.stats_path = 'models/win_rates.pkl'
        
        # 2. Carregamento seguro (Isso corrige o seu AttributeError!)
        if not os.path.exists(self.model_path):
            print("⚠️ Aviso: Modelo V2 não encontrado. Rode o main.py (Opção 2) primeiro.")
            self.model = None
            self.model_columns = []
            self.team_stats = {}
        else:
            self.model = joblib.load(self.model_path)
            self.model_columns = joblib.load(self.cols_path)
            # AQUI ESTÁ A LINHA QUE FALTAVA NO SEU CÓDIGO ANTIGO:
            self.team_stats = joblib.load(self.stats_path) 

    def resolver_id_time(self, entrada):
        """Converte Nome ou ID (Versão Offline: Rápida e sem bloqueios de API)"""
        if not entrada or str(entrada).strip() == "":
            return None
        
        entrada = str(entrada).strip()

        # Se for ID numérico direto
        if entrada.isdigit():
            final_id = int(entrada)
            # Verifica se o ID existe nas colunas do modelo
            col_r = f"radiant_team_id_{final_id}"
            col_d = f"dire_team_id_{final_id}"
            if col_r in self.model_columns or col_d in self.model_columns:
                return final_id
            else:
                return None
        return None

    def prever(self, rad_heroes, dire_heroes, team_rad_nome=None, team_dire_nome=None):
        if not self.model:
            return 0.5, "❌ Erro: Modelo não carregado. Treine a V2 no main.py."

        team_rad_id = self.resolver_id_time(team_rad_nome)
        team_dire_id = self.resolver_id_time(team_dire_nome)

        input_data = {}
        
        # Adiciona o Win Rate dos times (Neutro 50% caso não ache o time)
        input_data['rad_team_wr'] = self.team_stats.get(team_rad_id, 0.5)
        input_data['dire_team_wr'] = self.team_stats.get(team_dire_id, 0.5)
        
        if team_rad_id: input_data[f'radiant_team_id_{team_rad_id}'] = 1
        if team_dire_id: input_data[f'dire_team_id_{team_dire_id}'] = 1
            
        # A NOVA MÁGICA: MÉTODO SIMÉTRICO (+1 / -1)
        for h_id in rad_heroes:
            col_name = f'hero_{int(h_id)}_adv'
            if col_name in self.model_columns:
                input_data[col_name] = 1
                
        for h_id in dire_heroes:
            col_name = f'hero_{int(h_id)}_adv'
            if col_name in self.model_columns:
                input_data[col_name] = -1

        # Cria a matriz zerada e preenche
        df_predict = pd.DataFrame(columns=self.model_columns)
        df_predict.loc[0] = 0 
        
        for col, valor in input_data.items():
            if col in df_predict.columns:
                df_predict.loc[0, col] = valor
        
        df_predict = df_predict[self.model_columns]

        # Predição Final
        prob = self.model.predict_proba(df_predict)[0][1]
        return prob, None


# ==========================================
# MENU INTERATIVO PARA TESTES NO TERMINAL
# ==========================================
def menu_interativo():
    predictor = DotaPredictor()
    
    print("\n" + "═"*50)
    print("      🧙‍♂️ SIMULADOR DOTA IA (MODO TERMINAL) 🧙‍♂️")
    print("═"*50)

    # Entrada de Dados
    t_rad = input("\nID do Time Radiant (Deixe em branco para Neutro): ")
    t_dire = input("ID do Time Dire (Deixe em branco para Neutro):    ")

    print("\n--- DRAFT RADIANT (Digite apenas IDs numéricos, ex: 14) ---")
    r_h = [input(f"Slot {i+1} ID: ") for i in range(5)]

    print("\n--- DRAFT DIRE (Digite apenas IDs numéricos, ex: 120) ---")
    d_h = [input(f"Slot {i+1} ID: ") for i in range(5)]

    print("\n🧠 Analisando padrões históricos...")
    chance, erro = predictor.prever(r_h, d_h, t_rad, t_dire)

    if erro:
        print(f"❌ Erro na simulação: {erro}")
    else:
        print("\n" + "█"*45)
        print(f"  PROBABILIDADE RADIANT: {chance*100:.2f}%")
        print(f"  PROBABILIDADE DIRE:    {(1-chance)*100:.2f}%")
        print("█"*45)
        
        if abs(chance - 0.5) < 0.03:
            print("\n⚠️ Confronto equilibrado! O resultado dependerá dos detalhes in-game.")
        else:
            favorito = "RADIANT" if chance > 0.5 else "DIRE"
            print(f"\n🔥 Vantagem estatística para: {favorito}")

if __name__ == "__main__":
    while True:
        menu_interativo()
        if input("\nDeseja realizar outro teste? (s/n): ").lower() != 's':
            print("\nEncerrando simulador. GG WP!")
            break