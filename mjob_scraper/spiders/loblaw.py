import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

def load_exclude_words(filename="exclude_words.txt"):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

class loblawspider(scrapy.Spider):
    name = "loblaw"
    start_urls = [
        "https://careers.loblaw.ca/jobs?location_name=canada&location_type=1&filter%5Bcategory%5D%5B0%5D=Administrative&filter%5Bcategory%5D%5B1%5D=Business%20Analytics&filter%5Bcategory%5D%5B2%5D=Digital%20%26%20Ecommerce&filter%5Bcategory%5D%5B3%5D=Finance&filter%5Bcategory%5D%5B4%5D=Merchandising&filter%5Bcategory%5D%5B5%5D=Product%20Development&filter%5Bcategory%5D%5B6%5D=Support%20Centre&filter%5Bcategory%5D%5B7%5D=Technology&filter%5Bcategory%5D%5B8%5D=Top%20Management&sort_by=update_date&page_number=1"
    ]

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
            wait = WebDriverWait(driver, 10)
            page_num = 1

            while page_num <= 10:
                print(f"📄 [PAGE] Scraping page {page_num}: {driver.current_url}")
                job_cards = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='jobs-list-only_jobs-list_item']")))
                print(f"🟦 [DEBUG] Found {len(job_cards)} job cards.")

                for card in job_cards:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, "a.results-list__item-title span")
                        title = title_elem.text.strip()

                        if any(word in title.lower() for word in self.exclude_words):
                            print(f"⛔ [SKIP] Excluded title: {title}")
                            continue

                        job_link = card.find_element(By.CSS_SELECTOR, "a.results-list__item-title").get_attribute("href")
                        full_link = f"https://careers.loblaw.ca{job_link}" if job_link.startswith("/") else job_link

                        print(f"✅ [YIELD] Title: {title}, Link: {full_link}")
                        yield {
                            "title": title,
                            "link": full_link
                        }
                        time.sleep(0.5)

                    except Exception as e:
                        print(f"❌ [ERROR] Skipping job card: {e}")

                try:
                    # Click next and wait for change
                    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'page-link-next') and @aria-disabled='false']")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    driver.execute_script("arguments[0].click();", next_btn)
                    
                    # Wait for DOM to refresh
                    wait.until(EC.staleness_of(job_cards[0]))
                    time.sleep(3)
                    page_num += 1

                except Exception:
                    print("🛑 [STOP] No more pages or failed to load next.")
                    break

            print(f"🏁 [SUMMARY] Finished scraping {page_num} pages.")

        finally:
            driver.quit()
