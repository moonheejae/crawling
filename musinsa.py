import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import sqlite3
import json

class MusinsaCrawler:
    def __init__(self, db_path='musinsa_data.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        self.products = []
        self.item_count = 0

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image TEXT,
            name TEXT,
            price TEXT,
            brand TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    async def scroll_page(self, page, scroll_delay=1000, scroll_step=1000):
        scroll_pos = 0
        prev_height = await page.evaluate('document.body.scrollHeight')
        while True:
            await page.evaluate(f'window.scrollTo(0, {scroll_pos})')
            await page.wait_for_timeout(scroll_delay)
            scroll_pos += scroll_step
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == prev_height:
                break
            prev_height = new_height

        await page.wait_for_timeout(2000)  # 추가 대기 시간

    async def get_image_url(self, image):
        image_url = await image.get_attribute('src')
        if not image_url:
            image_url = await image.get_attribute('data-src')
        return image_url

    async def save_to_db(self):
        query = "INSERT INTO products (image, name, price, brand) VALUES (?, ?, ?, ?)"
        self.conn.executemany(query, [(p['image'], p['name'], p['price'], p['brand']) for p in self.products])
        self.conn.commit()

    async def save_to_json(self, keyword):
        with open(f'musinsa_{keyword}.json', 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=4)

    async def save_to_csv(self, keyword):
        df = pd.DataFrame(self.products)
        df.to_csv(f'musinsa_{keyword}.csv', index=False)

    async def crawl_page(self, page, keyword):
        await self.scroll_page(page)

        items = await page.query_selector_all('[data-gtm-cd-18="summary_goods"]')
        for item in items:
            try:
                image = await item.query_selector('img')
                image_url = await self.get_image_url(image)
                name = await item.get_attribute('data-bh-content-nm')
                price = await item.get_attribute('data-price')
                brand = await item.get_attribute('data-brand')

                self.products.append({
                    'image': image_url,
                    'name': name,
                    'price': price,
                    'brand': brand
                })
                self.item_count += 1

                if self.item_count >= 100:
                    break
            except Exception as e:
                print(f"Error occurred while parsing item: {e}")

    async def musinsa_crawler(self, keyword, save_format='csv'):
        url = f"https://www.musinsa.com/search/musinsa/integration?q={keyword}&type=keyword"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector('[data-gtm-cd-18="summary_goods"]')

            while self.item_count < 100:
                await self.crawl_page(page, keyword)
                if self.item_count >= 100:
                    break

                # 페이지 네비게이션 처리
                next_button = await page.query_selector('a.next')
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                else:
                    break

            if save_format == 'csv':
                await self.save_to_csv(keyword)
            elif save_format == 'json':
                await self.save_to_json(keyword)
            elif save_format == 'db':
                await self.save_to_db()

            await browser.close()

    async def run(self, keywords, save_format='csv'):
        tasks = [self.musinsa_crawler(keyword, save_format) for keyword in keywords]
        await asyncio.gather(*tasks)
