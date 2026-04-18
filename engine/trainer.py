import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, confusion_matrix
import joblib
import os

class DotaTrainer:
    def __init__(self):
        self.model_path = 'models/draft_intelligence_v2.pkl'
        self.columns_path = 'models/model_columns.pkl'
        self.stats_path = 'models/win_rates.pkl'
        
        if not os.path.exists('models'):
            os.makedirs('models')

    def train_model(self, dataset_path):
        df = pd.read_csv(dataset_path)
        if df.empty: return None, {}

        # 1. ORDENAÇÃO TEMPORAL
        if 'start_time' in df.columns:
            df = df.sort_values('start_time')

        # 2. CÁLCULO DE WIN RATES (PESO DAS ORGANIZAÇÕES)
        all_teams = pd.concat([df['radiant_team_id'], df['dire_team_id']]).unique()
        team_stats = {}
        
        for team in all_teams:
            win_rad = len(df[(df['radiant_team_id'] == team) & (df['radiant_win'] == 1)])
            games_rad = len(df[df['radiant_team_id'] == team])
            win_dire = len(df[(df['dire_team_id'] == team) & (df['radiant_win'] == 0)])
            games_dire = len(df[df['dire_team_id'] == team])
            
            total_games = games_rad + games_dire
            team_stats[team] = (win_rad + win_dire) / total_games if total_games >= 3 else 0.5

        df['rad_team_wr'] = df['radiant_team_id'].map(team_stats)
        df['dire_team_wr'] = df['dire_team_id'].map(team_stats)
        joblib.dump(team_stats, self.stats_path)

       # 3. A GRANDE CORREÇÃO: Método Simétrico (+1 / -1)
        print("🔧 Reestruturando heróis (Método Simétrico +/- 1)...")
        hero_cols = [c for c in df.columns if 'hero' in c]
        rad_cols = [c for c in hero_cols if 'rad' in c or 'r_' in c]
        dire_cols = [c for c in hero_cols if 'dire' in c or 'd_' in c]

        # Cria um dicionário para evitar o aviso de performance do Pandas
        novas_colunas = {}
        for h_id in range(1, 150):
            rad_tem = df[rad_cols].isin([h_id]).any(axis=1).astype(int)
            dire_tem = df[dire_cols].isin([h_id]).any(axis=1).astype(int)
            
            # A mágica: +1 se Radiant pegou, -1 se Dire pegou, 0 se ninguém pegou
            novas_colunas[f'hero_{h_id}_adv'] = rad_tem - dire_tem

        # Junta tudo e remove as colunas velhas
        df = pd.concat([df, pd.DataFrame(novas_colunas)], axis=1)
        df.drop(columns=hero_cols, inplace=True, errors='ignore')

        # 4. ONE-HOT ENCODING DOS TIMES
        df_ml = pd.get_dummies(df, columns=['radiant_team_id', 'dire_team_id'])

        # Prepara Variáveis (Apenas WinRate, Times e a Sacola de Heróis)
        cols_finais = [c for c in df_ml.columns if '_adv' in c or 'team_id' in c or 'team_wr' in c]
        X = df_ml[cols_finais]
        y = df_ml['radiant_win']

        joblib.dump(list(X.columns), self.columns_path)

        # 5. DIVISÃO E BALANCEAMENTO
        split_idx = int(len(X) * 0.85)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        peso_balanceamento = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1

        # 6. TREINAMENTO AGRESSIVO (Freios soltos)
        model = xgb.XGBClassifier(
            n_estimators=500, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.8,
            reg_lambda=1, reg_alpha=0,
            scale_pos_weight=peso_balanceamento, eval_metric='logloss'
        )

        model.fit(X_train, y_train)
        
        # 7. AVALIAÇÃO DE DESEMPENHO
        acc = accuracy_score(y_test, model.predict(X_test))
        cm = confusion_matrix(y_test, model.predict(X_test))
        
        joblib.dump(model, self.model_path)
        
        return model, {'accuracy': acc, 'total_matches': len(df), 'features_count': len(X.columns)}