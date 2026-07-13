import time
from web3 import Web3

BSC_RPC_URL = "http://bsc-dataseed.binance.org/"

def conectar_blockchain():
    w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
    
    if w3.is_connected():
        print(" [✓] Conexión exitosa a Binance Smart Chain.")
        bloque_actual = w3.eth.block_number
        print(f"[i] Bloque actual en la red: {bloque_actual}")
        return w3
    else:
        print(f"[✗] Error: No se pudo conectar al nodo RPC.")
        return None

if __name__ == "__main__":
    print("--- Iniciando Fase 1: Inicializacion de escaner ---")
    w3_client = conectar_blockchain()
    