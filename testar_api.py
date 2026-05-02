import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

# 1. Carrega as variáveis de segurança do arquivo .env
load_dotenv()
private_key = os.getenv("POLY_PRIVATE_KEY")

if not private_key:
    print("❌ Erro: Chave privada (POLY_PRIVATE_KEY) não encontrada no arquivo .env!")
    exit()

def testar_polymarket():
    print("🔄 Conectando aos servidores da Polymarket...")
    
    # 2. Inicializa o cliente apontando para a rede principal da Polygon (ID 137)
    client = ClobClient(
        host="https://clob.polymarket.com", 
        key=private_key, 
        chain_id=137 
    )

    # 3. O Pulo do Gato: Derivar as credenciais L2
    # Isso pega sua chave da Polygon e gera uma chave de API exclusiva para a Polymarket
    print("🔐 Solicitando credenciais de API (L2)...")
    try:
        creds = client.create_or_derive_api_creds()
        client.set_api_creds(creds)
        print("✅ Credenciais geradas e vinculadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao gerar credenciais: {e}")
        return

    # 4. Testar a comunicação buscando dados reais
    print("📊 Buscando mercados ativos...")
    try:
        mercados = client.get_markets() # Busca uma lista geral de mercados
        
        if mercados and len(mercados) > 0:
            print(f"✅ Sucesso total! A API respondeu e retornou {len(mercados)} mercados.")
            print(f"👉 Exemplo do primeiro mercado encontrado: '{mercados[0].get('question', 'Sem título')}'")
        else:
            print("⚠️ Conexão feita, mas a lista de mercados retornou vazia.")
            
    except Exception as e:
        print(f"❌ Erro ao buscar os mercados: {e}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 INICIANDO TESTE DE CONEXÃO POLYMARKET")
    print("="*50)
    testar_polymarket()
    print("="*50 + "\n")