import pandas as pd

def processar_indicadores(df):
    # --- LEADING INDICATORS (Sinais Antecipados) ---
    
    # 1. Velocidade de Execução (O quão cedo o time agiu)
    # Se a primeira torre cai antes dos 8 min, é um sinal forte.
    df['is_early_tower'] = (df['first_tower_time'] < 480).astype(int)
    
    # 2. Domínio de XP (Wisdom Gap)
    # Se um time pegou as 2 runas (2-0), o impacto no nível 6 dos suportes é imenso.
    df['wisdom_advantage'] = df['wisdom_7m_rad'] - df['wisdom_dire_7m']
    
    # 3. Posse de Objetivo Crítico
    # Roshan antes dos 20 min (1200s) captado por quem?
    df['rad_early_roshan'] = ((df['first_roshan_team'] == 0) & (df['first_roshan_time'] < 1200)).astype(int)

    # --- COINCIDENT INDICATORS (Sinais de Estado Atual) ---
    # Quem detém o primeiro Shard costuma ditar as lutas de mid-game
    df['rad_first_shard_signal'] = (df['first_shard_team'] == 0).astype(int)

    return df