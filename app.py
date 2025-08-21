from flask import Flask, render_template, jsonify  # Импортируем Flask и вспомогательные функции для рендеринга и JSON-ответов  
import asyncio  # Для асинхронного выполнения запросов  
import ccxt.async_support as ccxt  # Асинхронная версия ccxt для работы с API MEXC  
  
app = Flask(__name__)  # Создаем экземпляр Flask-приложения  
  
# Адрес контракта токена COCA (для хранения, если понадобится)  
COCA_CONTRACT_ADDRESS = '0x7b12598e3616261df1c05ec28de0d2fb10c1f206'  
  
# Асинхронная функция для получения актуальной цены токена COCA на бирже MEXC  
async def fetch_coca_price():  
    exchange = ccxt.mexc()  # Создаем объект биржи MEXC  
    symbol = 'COCA/USDT'    # Символ торговой пары COCA к USDT на MEXC  
    try:  
        ticker = await exchange.fetch_ticker(symbol)  # Асинхронный запрос текущего тикера (цен)  
        await exchange.close()  # Корректно закрываем соединение с биржей  
        return ticker['last']   # Возвращаем последнюю цену  
    except Exception as e:  
        print(f"Ошибка при получении цены с MEXC: {e}")  
        return None  # В случае ошибки возвращаем None  
  
# Маршрут главной страницы — рендерит статический HTML (index.html) с фронтендом  
@app.route('/')  
def index():  
    return render_template('index.html')  # Возвращаем содержимое static/index.html (папка templates должна быть настроена)  
  
# API-эндпоинт, возвращающий цену токена в формате JSON  
@app.route('/price')  
def price():  
    # Для вызова асинхронной функции из синхронного маршрута используем asyncio.run (для простоты)  
    price = asyncio.run(fetch_coca_price())  
    if price is not None:  
        return jsonify({'price': price})  
    else:  
        return jsonify({'error': 'Не удалось получить цену'}), 500  # Возвращаем ошибку сервера  
  
if __name__ == '__main__':  
    # Запускаем Flask приложение на всех интерфейсах, порт 5000, с включенным режимом отладки  
    app.run(host='0.0.0.0', port=5000, debug=True)  
