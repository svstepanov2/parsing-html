import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from tqdm import tqdm
import pandas as pd
import json


ua = UserAgent()
url = 'https://books.toscrape.com'
headers = {'User-Agent': ua.chrome}
session = requests.session()
response = session.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')


category = soup.find('ul', {'class', 'nav nav-list'}).find_all('a')
category_list = {c.getText().strip(): url + '/' + c.get('href') for c in category[1:]}
category_data = {}
for category, link in category_list.items():
    books_in_category = []
    while True:
        page = session.get(link, headers=headers)
        soup_page = BeautifulSoup(page.text, 'html.parser')
        books_in_page = soup_page.find_all('article', ('class', 'product_pod'))
        for book in books_in_page:
            *_, folder, file = book.find('h3').find('a').get('href').split('/')
            full_url = url + f'/catalogue/{folder}/{file}'
            books_in_category.append(full_url)

        next = soup_page.find('li', {'class': "next"})
        if next:
            link = '/'.join(link.split('/')[:-1] + [next.find('a').get('href')])
        else:
            category_data[category] = books_in_category
            break


books_data = []
for category, books_in_category in tqdm(category_data.items()):
    for link in books_in_category:
        book = {}
        page = session.get(link, headers=headers)
        soup_page = BeautifulSoup(page.text, 'html.parser')
        book['category'] = category
        product_main = soup_page.find('div', ('class', 'product_main'))
        book['name'] = product_main.find('h1').getText(strip=True)
        book['url'] = link
        price = product_main.find('p', ('class', 'price_color')).getText(strip=True)
        price = price.replace(',', '.')
        try:
            book['price'] = float(re.sub(r'[^\d.]+', '', price))
        except:
            book['price'] = None
        available = product_main.find('p', ('class', 'instock availability')).getText(strip=True)
        try:
            book['available'] = int(re.sub(r'[^\d.]+', '', available))
        except ValueError:
            book['available'] = None
        description = soup_page.find_all('p')
        book['description'] = description[3].getText()
        books_data.append(book)


df = pd.DataFrame(books_data)
print(df.info())


with open('books.json', 'w', encoding='utf-8') as f:
    json.dump(books_data, f, ensure_ascii=False, indent=2)