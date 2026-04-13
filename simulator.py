import joblib
import pandas as pd
import requests
import os

class DotaPredictor:
    def __init__(self):
        # Caminhos dos arquivos gerados pelo trainer
        self.model_path = 'models/draft_intelligence_v1.pkl'
        self.cols_path = 'models/model_columns.pkl'
        
        # Carrega o mapeamento de heróis da API para conversão Nome -> ID
        self.heroes_map = self._load_heroes()
        
        if not os.path.exists(self.model_path):
            raise Exception("❌ Modelo não encontrado! Treine o sistema primeiro rodando o main.py.")
            
        self.model = joblib.load(self.model_path)
        self.model_columns = joblib.load(self.cols_path)

    def _load_heroes(self):
        """Busca lista de heróis da API para permitir busca por nome"""
        try:
            res = requests.get("https://api.opendota.com/api/heroes", timeout=10)
            if res.status_code == 200:
                return {h['localized_name'].lower(): h['id'] for h in res.json()}
            return {}
        except:
            print("⚠️ Erro ao conectar com API de heróis. Use IDs numéricos do Excel.")
            return {}

    def resolver_id_time(self, entrada):
        """Converte Nome ou ID, garantindo que o ID resultante existe no modelo."""
        if not entrada or str(entrada).strip() == "":
            return None
        
        entrada = str(entrada).strip()
        final_id = None

        # 1. Se for ID numérico direto
        if entrada.isdigit():
            final_id = int(entrada)
        
        # 2. Se for nome, busca na API
        else:
            try:
                print(f"🔍 Buscando ID para o time: {entrada}...")
                res = requests.get(f"https://api.opendota.com/api/teams", params={'q': entrada}, timeout=5)
                if res.status_code == 200:
                    teams = res.json()
                    if teams:
                        # Pega o primeiro resultado da busca
                        final_id = teams[0]['team_id']
            except:
                return None

        # --- VALIDAÇÃO CRUCIAL ---
        # Verifica se o ID (seja digitado ou buscado) existe nas colunas do modelo
        col_r = f"radiant_team_id_{final_id}"
        col_d = f"dire_team_id_{final_id}"
        
        if col_r in self.model_columns or col_d in self.model_columns:
            return final_id
        else:
            print(f"⚠️ Aviso: O ID {final_id} não foi encontrado no treinamento do modelo.")
            return None

    def resolver_id_heroi(self, entrada):
        """Identifica se a entrada é ID (número) ou Nome (texto) de herói"""
        entrada = str(entrada).strip()
        
        # Se digitou o ID direto (ex: 14)
        if entrada.isdigit():
            return int(entrada)
        
        # Se digitou o nome (ex: "Pudge"), busca no mapa carregado
        return self.heroes_map.get(entrada.lower())

    def prever(self, r_inputs, d_inputs, t_rad_input=None, t_dire_input=None):
        """Executa a lógica de predição baseada no estado atual do modelo"""
        
        # 1. Converter entradas de heróis para IDs
        r_ids = [self.resolver_id_heroi(h) for h in r_inputs]
        d_ids = [self.resolver_id_heroi(h) for h in d_inputs]

        if None in r_ids or None in d_ids:
            return None, "Um ou mais heróis não foram encontrados. Verifique o Excel ou a grafia."

        # 2. Resolver IDs dos Times
        id_rad = self.resolver_id_time(t_rad_input)
        id_dire = self.resolver_id_time(t_dire_input)

        # 3. Criar DataFrame zerado com todas as colunas que o modelo conhece
        df_input = pd.DataFrame(0, index=[0], columns=self.model_columns)

        # 4. Ativar colunas de Times (se o ID existir no modelo)
        if id_rad:
            col = f"radiant_team_id_{id_rad}"
            if col in df_input.columns: 
                df_input.at[0, col] = 1
                print(f"✅ Time Radiant ID {id_rad} mapeado com sucesso.")
        
        if id_dire:
            col = f"dire_team_id_{id_dire}"
            if col in df_input.columns: 
                df_input.at[0, col] = 1
                print(f"✅ Time Dire ID {id_dire} mapeado com sucesso.")

        # 5. Ativar colunas de Heróis (nas posições corretas)
        for i in range(5):
            r_col = f"r_hero_{i+1}_{r_ids[i]}"
            d_col = f"d_hero_{i+1}_{d_ids[i]}"
            
            if r_col in df_input.columns: df_input.at[0, r_col] = 1
            if d_col in df_input.columns: df_input.at[0, d_col] = 1

        # 6. Calcular Probabilidade com XGBoost
        prob = self.model.predict_proba(df_input)[0]
        return prob[1], None

def menu_interativo():
    # Instancia a classe DotaPredictor
    predictor = DotaPredictor()
    
    print("\n" + "═"*50)
    print("      🧙‍♂️ SIMULADOR DOTA IA - CLASSE: DotaPredictor 🧙‍♂️")
    print("═"*50)

    # Entrada de Dados
    t_rad = input("\nNome ou ID do Time Radiant: ")
    t_dire = input("Nome ou ID do Time Dire:    ")

    print("\n--- DRAFT RADIANT (Nome ou ID) ---")
    r_h = [input(f"Slot {i+1}: ") for i in range(5)]

    print("\n--- DRAFT DIRE (Nome ou ID) ---")
    d_h = [input(f"Slot {i+1}: ") for i in range(5)]

    print("\n🧠 Analisando padrões históricas...")
    chance, erro = predictor.prever(r_h, d_h, t_rad, t_dire)

    if erro:
        print(f"❌ Erro na simulação: {erro}")
    else:
        print("\n" + "█"*45)
        print(f"  PROBABILIDADE RADIANT: {chance*100:.2f}%")
        print(f"  PROBABILIDADE DIRE:    {(1-chance)*100:.2f}%")
        print("█"*45)
        
        # Dica extra baseada na confiança
        if abs(chance - 0.5) < 0.03:
            print("\n⚠️ Confronto equilibrado! O resultado dependerá dos detalhes in-game.")
        else:
            favorito = t_rad if chance > 0.5 else t_dire
            if not favorito or favorito.isdigit(): favorito = "Radiant" if chance > 0.5 else "Dire"
            print(f"\n🔥 Vantagem estatística para: {favorito.upper()}")

if __name__ == "__main__":
    while True:
        menu_interativo()
        if input("\nDeseja realizar outro teste? (s/n): ").lower() != 's':
            print("\nEncerrando simulador. Boa sorte nos jogos!")
            break