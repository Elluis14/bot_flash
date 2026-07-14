import time
from web3 import Web3

BSC_RPC_URL = "https://bsc-dataseed.binance.org/"

# 1. Direcciones oficiales V2 (Mainnet)
FACTORY_ADDRESS = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73" # PancakeSwap V2 Factory
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"    # Wrapped BNB
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"    # USDT (BEP20)

# 2. ABI de la Fábrica (Asegurado que esté definido)
MIN_FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# 3. ABI del Par con la corrección de uint256
MIN_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint256"},
            {"name": "_reserve1", "type": "uint256"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def conectar_blockchain():
    w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
    if w3.is_connected():
        print(" [✓] Conexión exitosa a Binance Smart Chain.")
        bloque_actual = w3.eth.block_number
        print(f" [i] Bloque actual en la red: {bloque_actual}")
        return w3
    else:
        print(" [✗] Error: No se pudo conectar al nodo RPC.")
        return None

def obtener_precio_pancakeswap(w3):
    try:
        # Formatear direcciones por seguridad
        factory_check = w3.to_checksum_address(FACTORY_ADDRESS)
        wbnb_check = w3.to_checksum_address(WBNB_ADDRESS)
        usdt_check = w3.to_checksum_address(USDT_ADDRESS)
        
        # 1. Instanciar la Fábrica y pedir la dirección del par BNB/USDT
        factory_contract = w3.eth.contract(address=factory_check, abi=MIN_FACTORY_ABI)
        pair_address = factory_contract.functions.getPair(wbnb_check, usdt_check).call()
        
        if pair_address == "0x0000000000000000000000000000000000000000":
            print(" [✗] Error: El par no existe en PancakeSwap V2.")
            return

        # 2. Instanciar el contrato del Par (Pool)
        pair_contract = w3.eth.contract(address=pair_address, abi=MIN_PAIR_ABI)
        
        # Obtener las reservas de tokens en el pool
        reserves = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()
        
        # Identificar cuál reserva pertenece a qué token
        if token0.lower() == wbnb_check.lower():
            reserva_wbnb = reserves[0]
            reserva_usdt = reserves[1]
        else:
            reserva_wbnb = reserves[1]
            reserva_usdt = reserves[0]
            
        # Ajustar decimales (WBNB tiene 18, USDT tiene 18 en BSC)
        wbnb_human = w3.from_wei(reserva_wbnb, 'ether')
        usdt_human = w3.from_wei(reserva_usdt, 'ether')
        
        # El precio es simplemente dividir la reserva de dólares entre la de BNB
        precio_usdt = usdt_human / wbnb_human
        
        print(f" [i] Dirección del Pool V2 detectada: {pair_address}")
        print(f" [i] Precio actual de BNB en PancakeSwap V2: ${precio_usdt:.2f} USDT")
        
    except Exception as e:
        print(f" [✗] Error al consultar el precio V2: {e}")

if __name__ == "__main__":
    print("--- Iniciando Fase 2: Monitor de Precios en Tiempo Real---")
    w3_client = conectar_blockchain()
    if w3_client:
        ultimo_bloque = 0
        print("[i] Iniciando bucle de monitoreo continuo...(Presiona Ctrl + C para detener)")
        print ("-" * 60)
        
        while True:
            try:
                #1. Revisamos el bloque actual en la red
                bloque_actual = w3_client.eth.block_number
                
                #2 Solo consultamos el precio si la blockchain avanzo a un nuevo bloque
                if bloque_actual != ultimo_bloque:
                    print(f"\n [•] Nuevo bloque detectado: #{bloque_actual}")
                    obtener_precio_pancakeswap(w3_client)
                    ultimo_bloque = bloque_actual
            
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n [!] Monitoreo detenido por el usuario. Saliendo...")
                break
            except Exception as e:
                print(f" [!] Error en el bucle: {e}")
                time.sleep(5) # Espera un poco más si hay un error de red antes de reintentar
                    
                
        
    