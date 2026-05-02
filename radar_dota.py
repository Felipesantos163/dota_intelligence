import requests
import json

def radar_cirurgico():
    # O slug exato retirado do seu link da Polymarket
    slug_alvo = "dota2-z10-sar1-2026-04-29"
    print(f"📡 Buscando o evento EXATO pelo slug: {slug_alvo}")
    
    url = f"https://gamma-api.polymarket.com/events?slug={slug_alvo}"
    
    try:
        res = requests.get(url)
        dados = res.json()
        
        if not dados:
            print("❌ Evento não encontrado. O link pode ter expirado ou mudado.")
            return
            
        evento = dados[0] if isinstance(dados, list) else dados
        
        print(f"\n✅ Evento Encontrado: {evento.get('title', 'Sem Título')}")
        
        # Vamos descobrir quais são as verdadeiras tags que eles usam!
        tags = evento.get('tags', [])
        print(f"🏷️ Tags secretas da Polymarket: {tags}")
        
        mercados = evento.get('markets', [])
        print(f"\n📚 O evento contém {len(mercados)} mercados. Analisando o status de cada um:\n")
        
        for m in mercados:
            pergunta = m.get('question', m.get('title', 'Sem pergunta'))
            ativo = m.get('active')
            fechado = m.get('closed')
            
            if ativo and not fechado:
                status = "🟢 ABERTO"
            elif not ativo and not fechado:
                status = "🟡 INATIVO (Mas não fechado)"
            else:
                status = "🔴 FECHADO"
                
            print(f"{status} | {pergunta}")
            print(f"    ↳ Variáveis -> active: {ativo} | closed: {fechado}")
            print("-" * 60)
            
    except Exception as e:
        print(f"Erro na conexão: {e}")

if __name__ == "__main__":
    radar_cirurgico()