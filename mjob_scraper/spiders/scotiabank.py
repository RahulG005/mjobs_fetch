import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
import os
from urllib.parse import urljoin  # ✅ NEW

def load_exclude_words(filename="exclude_words.txt"):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

class scotiabankspider(scrapy.Spider):
    name = "scotiabank"
    start_urls = [
        "https://jobs.scotiabank.com/search/?q=&locationsearch=canada&sortColumn=referencedate&sortDirection=desc"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()

    def parse(self, response):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            base_url = response.url.split('?')[0]  # ✅ NEW
            today_str = datetime.today().strftime('%b %d, %Y')  # ✅ CHANGED
            yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%b %d, %Y')  # ✅ CHANGED
            jobs_per_page = 25  # ✅ NEW
            page_num = 1
            job_count = 0
            stop_scraping = False  # ✅ NEW

            while not stop_scraping:  # ✅ CHANGED
                startrow = (page_num - 1) * jobs_per_page  # ✅ NEW
                paginated_url = f"{base_url}?q=&locationsearch=canada&sortColumn=referencedate&sortDirection=desc&startrow={startrow}"  # ✅ NEW
                print(f"📄 [PAGE] Scraping page {page_num}: {paginated_url}")
                driver.get(paginated_url)
                time.sleep(3)

                job_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'data-row')]")
                print(f"🟦 [DEBUG] Found {len(job_rows)} job rows on page {page_num}.")

                if not job_rows:
                    print("🛑 [INFO] No job rows found. Stopping.")  # ✅ NEW
                    break

                for row in job_rows:
                    try:
                        title_elem = row.find_element(By.XPATH, ".//div[contains(@class, 'jobdetail-phone')]//a[contains(@class, 'jobTitle-link')]")
                        title = title_elem.get_attribute("textContent").strip()
                        link = title_elem.get_attribute("href")
                        if not link.startswith("http"):
                            link = urljoin("https://jobs.scotiabank.com", link)  # ✅ CHANGED

                        date_elem = row.find_element(By.XPATH, ".//span[contains(@class, 'jobDate')]")
                        post_date = date_elem.text.strip()

                        print(f"🔎 [DEBUG] Title: '{title}' | Post Date: '{post_date}'")

                        if post_date not in [today_str, yesterday_str]:  # ✅ NEW
                            print(f"🛑 [STOP] Encountered older job post: {post_date}. Ending scrape.")  # ✅ NEW
                            stop_scraping = True  # ✅ NEW
                            break  # ✅ NEW

                        if not any(word.lower() in title.lower() for word in self.exclude_words):
                            print(f"✅ [MATCH] Yielding job: '{title}' | Date: '{post_date}'")
                            yield {
                                "title": title,
                                "link": link,
                                "date": post_date
                            }
                            job_count += 1
                        else:
                            print(f"🚫 [EXCLUDE] Job '{title}' filtered by exclude_words.")

                    except Exception as e:
                        print(f"❌ [ERROR] Failed to parse row: {e}")

                    time.sleep(2)

                page_num += 1  # ✅ CHANGED

            # ✅ NEW — Final summary log
            print(f"🏁 [SUMMARY] Total pages scraped: {page_num - 1}")
            print(f"📊 [SUMMARY] Total jobs yielded (from {today_str} or {yesterday_str}): {job_count}")

        finally:
            driver.quit()
