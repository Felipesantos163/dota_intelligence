from eth_account import Account
import secrets

def gerar_carteira_bot():
    # 1. Adiciona entropia extra (aleatoriedade) para garantir que sua chave seja única e impenetrável
    priv_key = "0x" + secrets.token_hex(32)
    
    # 2. Deriva a conta e o endereço público a partir da chave privada
    conta = Account.from_key(priv_key)
    
    print("\n" + "="*50)
    print(" 🤖 CARTEIRA DO BOT GERADA COM SUCESSO 🤖")
    print("="*50)
    print(f"Endereço Público : {conta.address}")
    print(f"Chave Privada    : {conta.key.hex()}")
    print("="*50)
    print("\n⚠️ AVISO CRÍTICO DE SEGURANÇA ⚠️")
    print("1. O Endereço Público é o que você usará para depositar POL e USDC.")
    print("2. A Chave Privada é a 'senha' do seu robô. NUNCA a mostre para ninguém.")
    print("3. Copie esses dados agora para o seu arquivo .env, pois eles não serão salvos no código.")

if __name__ == "__main__":
    gerar_carteira_bot()