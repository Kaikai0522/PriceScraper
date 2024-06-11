from flask import Flask, request, jsonify, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from operator import itemgetter

from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# 開啟網站要導向的網頁
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 讓結果的dictionary根據價錢排列
def extract_price(item):
    price_text = item.get('price', '')
    price = ''.join(filter(str.isdigit, price_text))
    return int(price) if price else float('inf')

# 爬取pchome商品資訊
def fetch_pchome(query, driver):
    driver.get(f"https://24h.pchome.com.tw/search/v3.3/?q={query}")
    items = driver.find_elements(By.CSS_SELECTOR, '.col3f')
    results = []
    for item in items[:15]:  # 限制前10项
        try:
            name = item.find_element(By.CSS_SELECTOR, '.prod_name').text
            price = item.find_element(By.CSS_SELECTOR, '.price').text
            link = item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            img_url = item.find_element(By.CSS_SELECTOR, '.prod_img img').get_attribute('src')

            results.append({"name": name, "price": price, "link": link, "image": img_url})
            # print(results.len())
            if len(results) >= 10:
                break
        except Exception as e:
            print(f"Error parsing item: {e}")
    results.sort(key=extract_price)
    # print(results)
    return results

#爬取momo商品資訊
def fetch_momo(query, driver):
    driver.get(f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={query}")
    items = driver.find_elements(By.CSS_SELECTOR, 'li[actiontype="11"]')
    # print(items)
    results = []
    for item in items[:15]:  # 限制前10项
        try:
            name = item.find_element(By.CSS_SELECTOR, '.prdName').text
            price = item.find_element(By.CSS_SELECTOR, '.price').text
            link = item.find_element(By.CSS_SELECTOR, '.goodsUrl').get_attribute('href')
            img_url = item.find_element(By.CSS_SELECTOR, '.prdImg').get_attribute('src')

            results.append({"name": name, "price": price, "link": link, "image": img_url})
            # print(results.len())
            if len(results) >= 10:
                break
        except Exception as e:
            print(f"Error parsing item: {e}")
    results.sort(key=extract_price)
    # print(results)
    return results

# 爬取yahoo商品資訊
def fetch_yahoo(query, driver):
    driver.get(f"https://tw.buy.yahoo.com/search/product?p={query}")
    driver.maximize_window()
    # 下滑讓圖片載入，否則會找不到圖片
    driver.execute_script("window.scrollTo(0, 1000)")
    driver.execute_script("window.scrollTo(0, 1000)")
    driver.execute_script("window.scrollTo(0, 1000)")
    items = driver.find_elements(By.CLASS_NAME, 'sc-1drl28c-1.cnHJYW')
    # print("items", items)
    results = []
    for item in items[:15]:  # 限制前10项
        try:
            name = item.find_element(By.CLASS_NAME, 'sc-dlyefy.sc-gKcDdr.sc-1drl28c-5.jHwfYO.ikfoIQ.jZWZIY').text
            price = item.find_element(By.CLASS_NAME, 'sc-rZrxA.bbCJmN').text
            link = item.get_attribute('href')
            img_url = item.find_element(By.TAG_NAME, 'img').get_attribute('src')

            results.append({"name": name, "price": price, "link": link, "image": img_url})
            # print(results.len())
            if len(results) >= 10:
                break
        except Exception as e:
            print(f"Error parsing item: {e}")
    results.sort(key=extract_price)
    # print(results)
    return results

# 接收到search request執行下列涵式
@app.route('/search')
def search():
    query = request.args.get('query')
    print(query)
    chrome_options = Options()
    # chrome_options.add_argument('headless')

    # 過濾掉ceritficate error
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    # 開瀏覽器之後一次搜尋完所有網站，避免反覆開關瀏覽器跑太慢
    pchome_results = fetch_pchome(query, driver)
    momo_results = fetch_momo(query, driver)
    yahoo_results = fetch_yahoo(query, driver)

    driver.quit()
    # 回傳json格式的商品清單
    return jsonify([
        {"site": "PChome 24小時購物", "items": pchome_results},
        {"site": "Momo 購物網", "items": momo_results},
        {"site": "Yahoo 購物中心", "items": yahoo_results},
    ])

if __name__ == '__main__':
    # fetch_yahoo("rtx4070")
    app.run(debug=True)