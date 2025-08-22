from flask import Flask, render_template, jsonify  
import ccxt  
from web3 import Web3  
  
app = Flask(__name__)  
  
# Конфигурация  
RPC_URL = 'https://polygon-rpc.com'  # RPC Polygon  
FACTORY_ADDRESS = '0x5757371414417b8c6caad45baef941abc7d3ab32'  # QuickSwap Factory  
TOKEN_COCA = Web3.to_checksum_address('0x7b12598e3616261df1c05ec28de0d2fb10c1f206')  
TOKEN_USDT = Web3.to_checksum_address('0xc2132d05d31c914a87c6611c10748aeb04b58e8f') 
  
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
  
# Инициализация web3  
web3 = Web3(Web3.HTTPProvider(RPC_URL))  
  
  
def get_mexc_price():  
    """  
    Получаем цену COCA/USDT с MEXC (синхронно)  
    """  
    try:  
        exchange = ccxt.mexc()  
        symbol = 'COCA/USDT'  
        ticker = exchange.fetch_ticker(symbol)  
        price = ticker['last']  
        exchange.close()  
        return price  
    except Exception as e:  
        print(f'Ошибка получения цены с MEXC: {e}')  
        return None  
  
  
def get_quickswap_pair():  
    """  
    Получаем адрес пула COCA/USDT на QuickSwap через Factory  
    """  
    try:  
        factory = web3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)  
        pair_address = factory.functions.getPair(TOKEN_COCA, TOKEN_USDT).call()  
        if pair_address == '0x0000000000000000000000000000000000000000':  
            print('Пул не найден.')  
            return None  
        return pair_address  
    except Exception as e:  
        print(f'Ошибка получения адреса пула: {e}')  
        return None  
  
  
def get_quickswap_price():  
    """  
    Получаем цену COCA/USDT с QuickSwap на основе резервов пула  
    """  
    try:  
        pair_address = get_quickswap_pair()  
        if pair_address is None:  
            return None  
        pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)  
        reserves = pair_contract.functions.getReserves().call()  
        reserve0, reserve1 = reserves[0], reserves[1]  
        token0 = pair_contract.functions.token0().call()  
        token1 = pair_contract.functions.token1().call()  
        if token0.lower() == TOKEN_COCA.lower():  
            if reserve0 == 0:  
                return None  
            price = reserve1 / reserve0  
        elif token1.lower() == TOKEN_COCA.lower():  
            if reserve1 == 0:  
                return None  
            price = reserve0 / reserve1  
        else:  
            return None  
        return price  
    except Exception as e:  
        print(f'Ошибка получения цены с QuickSwap: {e}')  
        return None  
  
  
@app.route('/')  
def index():  
    return render_template('index.html')  
  
  
@app.route('/price')  
def price():  
    mexc_price = get_mexc_price()  
    quickswap_price = get_quickswap_price()  
    return jsonify({  
        'mexc': mexc_price if mexc_price is not None else 'Ошибка',  
        'quickswap': quickswap_price if quickswap_price is not None else 'Ошибка'  
    })  
  
  
if __name__ == '__main__':  
    app.run(host='0.0.0.0', port=5000) 
