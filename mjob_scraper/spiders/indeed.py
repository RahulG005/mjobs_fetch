import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import os


def load_exclude_words(filename="exclude_words.txt"):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


class IndeedSpider(scrapy.Spider):
    name = "indeed"
    start_urls = ["https://ca.indeed.com/jobs?q=data+analyst%2Cexcel%2C+business+analyst%2Canalysis%2C+entry+level%2C+junior%2C+Power+BI%2C+dashboard%2C+reporting%2C+data+insights%2C+support+analyst%2C+technical+support%2C+IT+support%2C+customer+support&sc=0kf%3Aattr%28CF3CP%29%3B&fromage=1&lang=en&vjk=8b52a48f4bbb970a"]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()
    
    def parse(self, response):
        
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get(response.url)
            time.sleep(3)  # wait for JS to load
            page_num = 1
            
            while True:
                print(f"📄 [PAGE] Scraping page {page_num}")
                jobs = driver.find_elements(By.XPATH, "//a[contains(@class, 'jcs-JobTitle')]")
                print(f"🟦 [DEBUG] Found {len(jobs)} job elements on page {page_num}.")

                for job in jobs:
                    title = job.text.strip()
                    if not title:
                        continue
                    print(f"🟩 [DEBUG] Extracted job title: '{title}'")

                    if not any(word.lower() in title.lower() for word in self.exclude_words):
                        try:
                            link = job.get_attribute("href")
                            print(f"✅ [MATCH] Yielding job: '{title}' | Link: {link}")
                            yield {
                                "title": title,
                                "link": link
                            }
                        except Exception as e:
                            print(f"❌ [ERROR] Failed to extract link for job '{title}': {e}")
                    else:
                        print(f"⏭️ [SKIP] Job '{title}' filtered out by exclude list.")
                    time.sleep(1)  # avoid bot detection
                    
                try:
                    next_btn = driver.find_element(By.XPATH, "//a[@aria-label='Next page']")
                    next_href = next_btn.get_attribute("href")
                    if not next_href:
                        print("🛑 [INFO] 'Next' button has no href — stopping pagination.")
                        break
                    print(f"➡️ [DEBUG] Navigating to next page: {next_href}")
                    driver.get(next_href)
                    page_num += 1
                    time.sleep(3)
                except Exception:
                    print("🛑 [INFO] 'Next' button not found — likely last page.")
                    break
            print(f"🏁 [SUMMARY] Total pages scraped: {page_num}")

        finally:
            driver.quit()
        