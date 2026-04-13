import pandas as pd
import requests
import os
import time

def buscar_nome_time(team_id):
    """Busca o nome de um time específico pelo ID"""
    try:
        # Rota direta para informações do time
        url = f"https://api.opendota.com/api/teams/{team_id}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('name', "Nome não encontrado")
    except:
        return "Erro na busca"
    return "N/A"

def gerar_excel_referencia():
    print("🚀 Iniciando extração de dados completa...")

    # 1. HERÓIS
    print("📥 Buscando nomes dos heróis...")
    try:
        res_h = requests.get("https://api.opendota.com/api/heroes")
        df_heroes = pd.DataFrame(res_h.json())[['id', 'localized_name']]
        df_heroes.columns = ['ID do Herói', 'Nome do Herói']
    except:
        df_heroes = pd.DataFrame()

    # 2. TIMES
    dataset_path = 'data/dataset_pro_v2.csv'
    if os.path.exists(dataset_path):
        df_data = pd.read_csv(dataset_path)
        
        # Contar quantas partidas cada time tem (Radiant + Dire)
        all_teams = pd.concat([df_data['radiant_team_id'], df_data['dire_team_id']])
        counts = all_teams.value_counts().reset_index()
        counts.columns = ['ID do Time', 'Total de Partidas']
        
        print(f"🔍 Encontrados {len(counts)} times. Buscando nomes (isso levará alguns minutos)...")
        
        nomes = []
        for i, row in counts.iterrows():
            tid = int(row['ID do Time'])
            print(f"[{i+1}/{len(counts)}] Buscando nome para ID: {tid}...", end="\r")
            
            nome = buscar_nome_time(tid)
            nomes.append(nome)
            
            # Pausa pequena para não ser bloqueado pela API (Rate Limit)
            time.sleep(0.5) 
            
        counts['Nome do Time'] = nomes
        df_teams = counts[['ID do Time', 'Nome do Time', 'Total de Partidas']]
    else:
        df_teams = pd.DataFrame()

    # 3. SALVAR
    arquivo_saida = 'Dota_Referencia_Total.xlsx'
    try:
        with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
            df_heroes.to_excel(writer, sheet_name='Heróis', index=False)
            if not df_teams.empty:
                df_teams.to_excel(writer, sheet_name='Times', index=False)
        
        print(f"\n\n✅ EXCEL GERADO: {arquivo_saida}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar: {e}")

if __name__ == "__main__":
    gerar_excel_referencia()