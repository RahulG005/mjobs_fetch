import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from selenium.webdriver.chrome.service import Service
import time
import os

def load_exclude_words(filename="exclude_words.txt"):
    # Get the absolute path to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


class cibcspider(scrapy.Spider):
    name = "cibc"
    start_urls = ["https://cibc.wd3.myworkdayjobs.com/search?Country=a30a87ed25634629aa6c3958aa2b91ea&timeType=382086945f8001182c270bf1860a7f00"]

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

            today = datetime.today().strftime('%b %d, %Y')
            page_num = 1

            while True:
                print(f"📄 [PAGE] Scraping page {page_num}")
                jobs = driver.find_elements(By.XPATH, "//a[@data-automation-id='jobTitle']")
                print(f"🟦 [DEBUG] Found {len(jobs)} job elements on page {page_num}.")

                for job in jobs:
                    title = job.text.strip()
                    print(f"🟩 [DEBUG] Extracted job title: '{title}'")
                    if not any(word.lower() in title.lower() for word in self.exclude_words):
                        try:
                            job_card = job.find_element(By.XPATH, "./ancestor::li[.//a[@data-automation-id='jobTitle']]")
                            date_elem = job_card.find_element(By.XPATH, ".//div[@data-automation-id='postedOn']//dd")
                            post_date = date_elem.text.strip().lower()
                            print(f"🔎 [DEBUG] Title: '{title}' | Post Date: '{post_date}'")
                        except Exception as e:
                            print(f"❌ [ERROR] Exception for job '{title}': {e}")
                            post_date = ""

                        if "yesterday" in post_date or "today" in post_date or today in post_date:
                            print(f"✅ [MATCH] Yielding job: '{title}' | Date: '{post_date}'")
                            yield {
                                "title": title,
                                "link": job.get_attribute("href"),
                                "date": post_date
                            }
                        else:
                            print(f"⏭️ [SKIP] Job '{title}' does not match date filter. Post Date: '{post_date}'")
                    time.sleep(1)  # delay between processing jobs to avoid rapid scraping

                try:
                    next_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'next')]")
                    print(f"➡️ [DEBUG] Found Next button. Classes: {next_btn.get_attribute('class')}")
                    if "disabled" in next_btn.get_attribute("class"):
                        break
                    next_btn.click()
                    page_num += 1  # Increment page counter
                    time.sleep(3)  # wait for next page to load
                except Exception:
                    print("🛑 [INFO] 'Next' button not found. Likely reached the last page of results.")
                    break
                
            print(f"🏁 [SUMMARY] Total pages scraped: {page_num}")
            
        finally:
            driver.quit()

