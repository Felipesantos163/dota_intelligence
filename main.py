import sys
import os
import time
import requests
import pandas as pd
import urllib.parse
import joblib

# Setup de pastas
for folder in ['data', 'models', 'plots']:
    if not os.path.exists(folder): os.makedirs(folder)

from engine.collector import DotaCollector
from engine.trainer import DotaTrainer

# CONFIGURAÇÕES
LIMITE_BUSCA = 6000    # Quantas partidas buscar na API por vez
INTERVALO_API = 1.1   # Delay entre partidas
DATASET_PATH = 'data/dataset_pro_v2.csv'

def buscar_partidas_recentes(limite=6000):
    print(f"🔍 [1/4] Buscando histórico de partidas profissionais (SQL)...")
    
    # QUERY SQL para buscar partidas profissionais.
    # ou simplesmente expande o horizonte de tempo.
    sql = f"""
    SELECT 
        match_id, 
        radiant_team_id, 
        dire_team_id 
    FROM matches 
    WHERE leagueid > 0 
    AND radiant_team_id IS NOT NULL 
    AND dire_team_id IS NOT NULL
    AND start_time > (extract(epoch from now()) - 7776000) -- Últimos 90 dias
    ORDER BY match_id DESC 
    LIMIT {limite}
    """
    
    query_encoded = urllib.parse.quote(sql)
    url = f"https://api.opendota.com/api/explorer?sql={query_encoded}"
    
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            data = res.json()
            if 'rows' in data:
                print(f"✅ {len(data['rows'])} partidas encontradas no banco de dados!")
                return data['rows']
        
        print(f"⚠️ Explorer não retornou dados (Status {res.status_code}).")
        return []
    except Exception as e:
        print(f"❌ Erro ao acessar histórico: {e}")
        return []

def salvar_dados(novos_dados):
    if not novos_dados: return
    df_novo = pd.DataFrame(novos_dados)
    if os.path.exists(DATASET_PATH):
        df_antigo = pd.read_csv(DATASET_PATH)
        df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
        df_final.drop_duplicates(subset=['match_id'], keep='last', inplace=True)
        df_final.to_csv(DATASET_PATH, index=False)
    else:
        df_novo.to_csv(DATASET_PATH, index=False)

def iniciar_sistema():
    # 1. Busca IDs
    lista_api = buscar_partidas_recentes(LIMITE_BUSCA)
    if not lista_api: return

    # 2. Filtra o que já temos
    ids_ja_minerados = set()
    if os.path.exists(DATASET_PATH):
        df_temp = pd.read_csv(DATASET_PATH, usecols=['match_id'])
        ids_ja_minerados = set(df_temp['match_id'].unique())
    
    partidas_para_minerar = [p for p in lista_api if p['match_id'] not in ids_ja_minerados]
    
    print(f"📊 Total na API: {len(lista_api)} | Já temos: {len(ids_ja_minerados)}")
    print(f"🚀 [2/4] Minerando {len(partidas_para_minerar)} novas partidas...")

    if partidas_para_minerar:
        collector = DotaCollector()
        lote = []
        
        for i, row in enumerate(partidas_para_minerar):
            dados = collector.process_match_deep(row['match_id'])
            if dados:
                # Injetamos os IDs dos times vindo da busca inicial
                dados['radiant_team_id'] = row['radiant_team_id']
                dados['dire_team_id'] = row['dire_team_id']
                lote.append(dados)
                print(f"[{i+1}/{len(partidas_para_minerar)}] Partida {row['match_id']} OK", end="\r")
            
            # Salva de 10 em 10 para não perder progresso
            if (i + 1) % 10 == 0:
                salvar_dados(lote)
                lote = []
            
            time.sleep(INTERVALO_API)
        
        salvar_dados(lote) # Salva o restante

    # 3. Treinamento
    print("\n🧠 [3/4] Treinando modelo com base acumulada...")
    trainer = DotaTrainer()
    model, metrics = trainer.train_model(DATASET_PATH)
    
    print("\n" + "="*40)
    print(f"🏆 SUCESSO! Precisão: {metrics.get('accuracy', 0)*100:.2f}%")
    print(f"Base de dados total: {len(pd.read_csv(DATASET_PATH))} partidas.")
    print("="*40)

if __name__ == "__main__":
    iniciar_sistema()