from flask import Flask, render_template, jsonify  
import asyncio  
import ccxt.async_support as ccxt  
from web3 import Web3  
  
app = Flask(__name__)  
  
# Конфигурация  
RPC_URL = 'https://polygon-rpc.com'  # RPC Polygon  
INFURA_ID = ''  # Если нужен, можно убрать, сейчас не используется  
DEX_RPC_URL = RPC_URL  # Используем RPC Polygon  
  
# Factory контракт QuickSwap (аналог Uniswap V2) на Polygon  
FACTORY_ADDRESS = '0x5757371414417b8c6caad45baef941abc7d3ab32'  
  
# ABI только для getPair функции  
FACTORY_ABI = [  
    {  
        "inputs": [  
            {"internalType": "address", "name": "tokenA", "type": "address"},  
            {"internalType": "address", "name": "tokenB", "type": "address"}  
        ],  
        "name": "getPair",  
        "outputs": [  
            {"internalType": "address", "name": "pair", "type": "address"}  
        ],  
        "stateMutability": "view",  
        "type": "function"  
    }  
]  
  
# Адреса токенов COCA и USDT в Polygon сети  
TOKEN_COCA = Web3.toChecksumAddress('0x7b12598e3616261df1c05ec28de0d2fb10c1f206')  
TOKEN_USDT = Web3.toChecksumAddress('0xc2132d05d31c914a87c6611c10748aeb04b58e8f')  
  
# ABI для пары UniswapV2 (QuickSwap) с getReserves, token0, token1  
PAIR_ABI = [  
    {  
        "constant": True,  
        "inputs": [],  
        "name": "getReserves",  
        "outputs": [  
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},  
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},  
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}  
        ],  
        "payable": False,  
        "stateMutability": "view",  
        "type": "function"  
    },  
    {  
        "constant": True,  
        "inputs": [],  
        "name": "token0",  
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],  
        "payable": False,  
        "stateMutability": "view",  
        "type": "function"  
    },  
    {  
        "constant": True,  
        "inputs": [],  
        "name": "token1",  
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],  
        "payable": False,  
        "stateMutability": "view",  
        "type": "function"  
    }  
]  
  
  
async def fetch_coca_price_mexc():  
    """Асинхронно получить цену COCA/USDT с биржи MEXC через ccxt"""  
    exchange = ccxt.mexc()  
    symbol = 'COCA/USDT'  
    try:  
        ticker = await exchange.fetch_ticker(symbol)  
        await exchange.close()  
        return ticker['last']  
    except Exception as e:  
        print(f"MEXC price fetch error: {e}")  
        return None  
  
  
def get_uniswap_pair_address(web3, tokenA, tokenB):  
    """  
    Получить адрес пула пары tokenA-tokenB через Factory контракт  
    """  
    factory = web3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)  
    return factory.functions.getPair(tokenA, tokenB).call()  
  
  
def fetch_coca_price_uniswap_sync():  
    """  
    Синхронно получить цену COCA в USDT с пула QuickSwap на Polygon.  
    Возвращает float цену или None при ошибках.  
    """  
    try:  
        web3 = Web3(Web3.HTTPProvider(DEX_RPC_URL))  
        pair_address = get_uniswap_pair_address(web3, TOKEN_COCA, TOKEN_USDT)  
  
        if pair_address == '0x0000000000000000000000000000000000000000':  
            print("Пул COCA/USDT не найден на QuickSwap")  
            return None  
  
        pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)  
          
        reserves = pair_contract.functions.getReserves().call()  
        reserve0, reserve1 = reserves[0], reserves[1]  
  
        token0 = pair_contract.functions.token0().call()  
        token1 = pair_contract.functions.token1().call()  
  
        # Определяем в какой переменной какой токен  
        if token0.lower() == TOKEN_COCA.lower():  
            if reserve0 == 0:  
                return None  
            price = reserve1 / reserve0  # цена COCA в USDT  
        elif token1.lower() == TOKEN_COCA.lower():  
            if reserve1 == 0:  
                return None  
            price = reserve0 / reserve1  
        else:  
            # COCA не найдена в паре (маловероятно)  
            return None  
  
        return float(price)  
    except Exception as e:  
        print(f"Uniswap price fetch error: {e}")  
        return None  
  
  
@app.route('/')  
def index():  
    # Отдаём фронтенд  
    return render_template('index.html')  
  
  
@app.route('/price')  
def price():  
    # Асинхронно вызываем API MEXC, синхронно - пул QuickSwap  
    mexc_price = None  
    uniswap_price = None  
  
    async def get_prices():  
        nonlocal mexc_price  
        mexc_price = await fetch_coca_price_mexc()  
  
    asyncio.run(get_prices())  
    uniswap_price = fetch_coca_price_uniswap_sync()  
  
    result = {  
        'mexc': mexc_price if mexc_price is not None else 'Ошибка получения',  
        'uniswap': uniswap_price if uniswap_price is not None else 'Ошибка получения'  
    }  
    return jsonify(result)  
  
  
if __name__ == '__main__':  
    app.run(host='0.0.0.0', port=5000, debug=True)  
