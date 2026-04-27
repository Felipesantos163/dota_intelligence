import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
import joblib
import os

class DotaTrainer:
    def __init__(self):
        if not os.path.exists('models'):
            os.makedirs('models')
        self.stats_path = 'models/win_rates.pkl'

    def preparar_dados(self, df):
        if 'start_time' in df.columns:
            df = df.sort_values('start_time')

        # 1. Calcula Win Rates das organizações
        all_teams = pd.concat([df['radiant_team_id'], df['dire_team_id']]).unique()
        team_stats = {}
        for team in all_teams:
            jogos = df[(df['radiant_team_id'] == team) | (df['dire_team_id'] == team)]
            vitorias = len(jogos[(jogos['radiant_team_id'] == team) & (jogos['radiant_win'] == 1)]) + \
                       len(jogos[(jogos['dire_team_id'] == team) & (jogos['radiant_win'] == 0)])
            team_stats[team] = vitorias / len(jogos) if len(jogos) >= 3 else 0.5

        df['rad_team_wr'] = df['radiant_team_id'].map(team_stats)
        df['dire_team_wr'] = df['dire_team_id'].map(team_stats)
        joblib.dump(team_stats, self.stats_path)

        # 2. Heróis Simétricos (+1 Radiant, -1 Dire)
        print("🔧 Estruturando heróis...")
        hero_cols = [c for c in df.columns if 'hero' in c]
        rad_cols = [c for c in hero_cols if 'r_' in c or 'rad' in c]
        dire_cols = [c for c in hero_cols if 'd_' in c or 'dire' in c]

        novas_colunas = {}
        for h_id in range(1, 150):
            rad_tem = df[rad_cols].isin([h_id]).any(axis=1).astype(int)
            dire_tem = df[dire_cols].isin([h_id]).any(axis=1).astype(int)
            novas_colunas[f'hero_{h_id}_adv'] = rad_tem - dire_tem

        df = pd.concat([df, pd.DataFrame(novas_colunas)], axis=1)
        
        # 3. One-Hot Encoding
        return pd.get_dummies(df, columns=['radiant_team_id', 'dire_team_id'])

    def treinar_modelo_especifico(self, df, alvo, caminho_modelo, caminho_cols):
        print(f"\n🧠 Treinando alvo: {alvo}...")
        
        # Remove partidas onde o evento não ocorreu (-1)
        df_valido = df[df[alvo].isin([0, 1])].copy()
        
        if len(df_valido) == 0:
            print(f"⚠️ Sem dados suficientes para {alvo}. Treino pulado.")
            return 0
        
        # Padroniza: Radiant sucesso = 1, Dire sucesso = 0
        if alvo != 'radiant_win':
            df_valido[alvo] = (df_valido[alvo] == 0).astype(int)

        cols_treino = [c for c in df_valido.columns if '_adv' in c or 'team_id' in c or 'team_wr' in c]
        X = df_valido[cols_treino]
        y = df_valido[alvo]

        joblib.dump(list(X.columns), caminho_cols)

        # Split 85/15
        split = int(len(X) * 0.85)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

        peso = len(y_train[y_train == 0]) / len(y_train[y_train == 1]) if len(y_train[y_train == 1]) > 0 else 1

        # Treinamento
        modelo = xgb.XGBClassifier(n_estimators=500, max_depth=5, learning_rate=0.05,
                                   subsample=0.9, colsample_bytree=0.8,
                                   scale_pos_weight=peso, eval_metric='logloss')
        modelo.fit(X_train, y_train)

        # Tabela de Confiabilidade
        probs = modelo.predict_proba(X_test)[:, 1]
        df_calib = pd.DataFrame({'prob': probs, 'real': y_test})
        bins = [0.0, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 1.0]
        df_calib['faixa'] = pd.cut(df_calib['prob'], bins=bins)
        confiabilidade = df_calib.groupby('faixa', observed=True)['real'].mean().to_dict()
        joblib.dump(confiabilidade, caminho_modelo.replace('.pkl', '_conf.pkl'))

        acc = accuracy_score(y_test, modelo.predict(X_test))
        joblib.dump(modelo, caminho_modelo)
        
        print(f"✅ {alvo} Treinado! Precisão base: {acc*100:.1f}%")
        return acc

    def train_model(self, dataset_path):
        df = pd.read_csv(dataset_path)
        if df.empty: return None, {}
        
        df_ml = self.preparar_dados(df)
        
        # Treina os 3 alvos
        acc_win = self.treinar_modelo_especifico(df_ml, 'radiant_win', 'models/draft_intelligence_v2.pkl', 'models/model_columns.pkl')
        self.treinar_modelo_especifico(df_ml, 'first_blood_team', 'models/first_blood_v1.pkl', 'models/fb_columns.pkl')
        self.treinar_modelo_especifico(df_ml, 'first_tower_team', 'models/first_tower_v1.pkl', 'models/ft_columns.pkl')

        return True, {'accuracy': acc_win, 'total_matches': len(df), 'features_count': len(df_ml.columns)}