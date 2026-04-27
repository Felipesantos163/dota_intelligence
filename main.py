import sys
import os
import time
import requests
import pandas as pd
import urllib.parse

# Setup inicial de pastas
for folder in ['data', 'models', 'plots']:
    if not os.path.exists(folder): os.makedirs(folder)

from engine.collector import DotaCollector
from engine.trainer import DotaTrainer

# CONFIGURAÇÕES
LIMITE_BUSCA = 2900    
INTERVALO_API = 1.0   
DATASET_PATH = 'data/dataset_pro_v2.csv'

# ==========================================
# MÓDULO 1: MINERADOR (COLETA DE DADOS)
# ==========================================
def buscar_partidas_recentes(limite=3000):
    print(f"\n🔍 Buscando histórico de partidas profissionais no OpenDota...")
    
    sql = f"""
    SELECT 
        match_id, 
        radiant_team_id, 
        dire_team_id 
    FROM matches 
    WHERE leagueid > 0 
    AND radiant_team_id IS NOT NULL 
    AND dire_team_id IS NOT NULL
    AND start_time > (extract(epoch from now()) - 7776000)
    ORDER BY match_id DESC 
    LIMIT {limite}
    """
    
    query_encoded = urllib.parse.quote(sql)
    url = f"https://api.opendota.com/api/explorer?sql={query_encoded}"
    
    try:
        res = requests.get(url, timeout=60)
        if res.status_code == 200:
            data = res.json()
            if 'rows' in data:
                print(f"✅ {len(data['rows'])} partidas encontradas no banco SQL da API!")
                return data['rows']
        print(f"⚠️ API Explorer falhou (Status {res.status_code}).")
        return []
    except Exception as e:
        print(f"❌ Erro de conexão ao buscar histórico: {e}")
        return []

def salvar_dados(novos_dados):
    if not novos_dados: return
    df_novo = pd.DataFrame(novos_dados)
    if os.path.exists(DATASET_PATH):
        try:
            df_antigo = pd.read_csv(DATASET_PATH)
            df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            df_final.drop_duplicates(subset=['match_id'], keep='last', inplace=True)
            df_final.to_csv(DATASET_PATH, index=False)
        except Exception as e:
            print(f"❌ Erro ao salvar (O arquivo CSV pode estar corrompido ou aberto): {e}")
    else:
        df_novo.to_csv(DATASET_PATH, index=False)

def executar_minerador():
    lista_api = buscar_partidas_recentes(LIMITE_BUSCA)
    if not lista_api: return

    ids_ja_minerados = set()
    if os.path.exists(DATASET_PATH):
        try:
            df_temp = pd.read_csv(DATASET_PATH, usecols=['match_id'])
            ids_ja_minerados = set(df_temp['match_id'].unique())
        except:
            pass # Se o arquivo estiver vazio ou com erro, ignora
    
    partidas_para_minerar = [p for p in lista_api if p['match_id'] not in ids_ja_minerados]
    
    print(f"📊 Base Local: {len(ids_ja_minerados)} partidas | Novas detectadas: {len(partidas_para_minerar)}")
    
    if not partidas_para_minerar:
        print("✨ Sua base de dados já está 100% atualizada com as partidas recentes!")
        return

    print(f"🚀 Iniciando download de {len(partidas_para_minerar)} novas partidas...\n")
    collector = DotaCollector()
    lote = []
    
    for i, row in enumerate(partidas_para_minerar):
        # Proteção contra erros de Timeout durante o loop longo
        try:
            dados = collector.process_match_deep(row['match_id'])
            if dados:
                dados['radiant_team_id'] = row['radiant_team_id']
                dados['dire_team_id'] = row['dire_team_id']
                lote.append(dados)
                print(f"📥 [{i+1}/{len(partidas_para_minerar)}] Match {row['match_id']} -> OK", end="\r")
        except Exception as e:
            print(f"\n⚠️ Pulo de segurança no ID {row['match_id']} (Erro: {e})")

        if (i + 1) % 10 == 0:
            salvar_dados(lote)
            lote = []
        
        time.sleep(INTERVALO_API)
    
    salvar_dados(lote)
    print("\n✅ Mineração finalizada com sucesso!")


# ==========================================
# MÓDULO 2: TREINADOR (MACHINE LEARNING)
# ==========================================
def executar_treinador():
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Erro: Arquivo {DATASET_PATH} não encontrado. Execute o Minerador primeiro!")
        return
        
    print("\n🧠 Iniciando treinamento do modelo XGBoost com dados locais...")
    try:
        trainer = DotaTrainer()
        model, metrics = trainer.train_model(DATASET_PATH)
        
        if model:
            print("\n" + "═"*45)
            print(f"🏆 TREINO CONCLUÍDO! PRECISÃO: {metrics.get('accuracy', 0)*100:.2f}%")
            print(f"📈 Total de partidas analisadas: {metrics.get('total_matches', 'N/A')}")
            print(f"🧩 Variáveis (Features): {metrics.get('features_count', 'N/A')}")
            print("═"*45)
            print("✨ Os arquivos em /models foram atualizados!")
    except Exception as e:
        print(f"\n❌ Falha crítica no treinamento: {e}")


# ==========================================
# MENU INTERATIVO
# ==========================================
def menu_principal():
    while True:
        print("\n" + "█"*40)
        print(" DOTA INTELLIGENCE CORE")
        print("█"*40)
        print("[1] 📥 Buscar Novas Partidas (Mineração)")
        print("[2] 🧠 Treinar Modelo (Machine Learning)")
        print("[3] 🚀 Fazer Tudo (Minerar e Treinar)")
        print("[0] ❌ Sair")
        3
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == '1':
            executar_minerador()
        elif escolha == '2':
            executar_treinador()
        elif escolha == '3':
            executar_minerador()
            executar_treinador()
        elif escolha == '0':
            print("Encerrando sistema. GG WP!")
            sys.exit(0)
        else:
            print("⚠️ Opção inválida. Digite um número de 0 a 3.")

if __name__ == "__main__":
    # Garante que o menu limpo apareça assim que rodar o script
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\nProcesso interrompido pelo usuário. GG!")
        sys.exit(0)