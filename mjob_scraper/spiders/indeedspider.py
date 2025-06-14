import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

class IndeedSpider(scrapy.Spider):
    name = "indeedspider"

    def __init__(self, *args, **kwargs):
        super(IndeedSpider, self).__init__(*args, **kwargs)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Read URLs from file
        with open("indeedlinklist.txt", "r") as f:
            self.start_urls = [line.strip() for line in f if line.strip()]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)

        page_num = 1

        while True:
            print(f"📄 [PAGE] Scraping page {page_num}")
            jobs = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'jcs-JobTitle')]")
            print(f"🟦 [DEBUG] Found {len(jobs)} job elements on page {page_num}.")

            for job in jobs:
                title = job.text.strip()
                if not title:
                    continue
                print(f"🟩 [DEBUG] Extracted job title: '{title}'")

                # Filter titles
                if not any(word.lower() in title.lower() for word in [
                    "Senior", "Application", "Co-Op", "Lead", "Director", "bilingual", "Engineer",
                    "Manager", "Testing", "finance", "financial", "III", "security", "IV",
                    "scientist", "personal", "portfolio", "sr.", "sr "
                ]):
                    try:
                        link = job.get_attribute("href")
                        print(f"✅ [MATCH] Yielding job: '{title}' | Link: {link}")
                        yield {
                            "title": title,
                            "link": link,
                        }
                    except Exception as e:
                        print(f"❌ [ERROR] Failed to extract link for job '{title}': {e}")
                else:
                    print(f"⏭️ [SKIP] Job '{title}' filtered out")

                time.sleep(1)

                try:
                    next_btn = self.driver.find_element(By.XPATH, "//a[@aria-label='Next page']")
                    next_href = next_btn.get_attribute("href")
                    if not next_href:
                        print("🛑 [INFO] 'Next' button has no href attribute — stopping pagination.")
                        break
                    print(f"➡️ [DEBUG] Navigating to next page: {next_href}")
                    self.driver.get(next_href)
                    page_num += 1
                    time.sleep(3)
                except Exception:
                    print("🛑 [INFO] 'Next' button not found — reached last page.")
                    break



        print(f"🏁 [SUMMARY] Total pages scraped: {page_num}")

    def closed(self, reason):
        if self.driver:
            self.driver.quit()
