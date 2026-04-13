import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

class DotaTrainer:
    def __init__(self):
        self.model_path = 'models/draft_intelligence_v1.pkl'
        self.columns_path = 'models/model_columns.pkl'
        
        # Garante que a pasta de modelos exista
        if not os.path.exists('models'):
            os.makedirs('models')

    def train_model(self, dataset_path):
        # 1. CARREGAMENTO
        df = pd.read_csv(dataset_path)
        
        if df.empty:
            print("❌ Erro: O dataset está vazio.")
            return None, {}

        # 2. LIMPEZA (Feature Selection)
        # Mantemos apenas o que o simulador conhece: Times e Heróis.
        # Ignoramos propositalmente GPM, Kills, Roshan e Duration para evitar Data Leakage.
        cols_essenciais = ['radiant_win', 'radiant_team_id', 'dire_team_id']
        cols_heroes = [c for c in df.columns if 'hero' in c]
        
        # Filtra o DataFrame
        df_ml = df[cols_essenciais + cols_heroes].copy()
        
        # 3. PRE-PROCESSAMENTO (One-Hot Encoding)
        # Transformamos IDs numéricos em colunas binárias (0 ou 1)
        # Ex: radiant_team_id_1838315 = 1
        cols_para_converter = ['radiant_team_id', 'dire_team_id'] + cols_heroes
        df_final = pd.get_dummies(df_ml, columns=cols_para_converter)

        # 4. DEFINIÇÃO DE ALVO E TREINO
        X = df_final.drop(columns=['radiant_win'])
        y = df_final['radiant_win']

        # CRITICAL: Salva a ordem das colunas para o Simulador ser idêntico ao Treino
        joblib.dump(list(X.columns), self.columns_path)

        # Divisão de base (80% treino / 20% teste)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 5. CONFIGURAÇÃO DO XGBOOST
        model = xgb.XGBClassifier(
            n_estimators=300,        # Quantidade de "árvores" de decisão
            max_depth=5,             # Profundidade (evita decorar demais os dados)
            learning_rate=0.05,      # Velocidade de aprendizado
            subsample=0.8,           # Usa 80% dos dados em cada rodada (evita vício)
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )

        # 6. TREINAMENTO
        print(f"⚙️ Treinando modelo com {len(X_train)} partidas e {len(X.columns)} variáveis...")
        model.fit(X_train, y_train)

        # 7. AVALIAÇÃO
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        # Salva o binário do modelo
        joblib.dump(model, self.model_path)
        
        metrics = {
            'accuracy': acc,
            'total_matches': len(df),
            'features_count': len(X.columns)
        }

        return model, metrics