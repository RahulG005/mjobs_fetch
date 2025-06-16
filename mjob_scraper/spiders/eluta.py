import scrapy
import os
import re
import time, random

def load_exclude_words(filename="exclude_words.txt"):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

class ElutaSpider(scrapy.Spider):
    name = "eluta"
    start_urls = [
        "https://www.eluta.ca/search?q=power+bi&salary_type=1&filter-salary=&filter-ef=&filter-field=&filter-eterm=&filter-etype=&filter-experience=&filter-remote_jobs=&filter-location=&filter-radius=&sort=post"
    ]

    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()
        self.stop_crawling = False
        self.page_num = 1

    def parse(self, response):
        print(f"📄 [PAGE] Scraping page {self.page_num}: {response.url}")
        time.sleep(random.uniform(2, 5))
        
        jobs = response.css("div.organic-job")
        print(f"🟦 [DEBUG] Found {len(jobs)} job elements on page {self.page_num}.")
        
        for job in jobs:
            job_a = job.css("a.lk-job-title")
            title = job_a.css("::text").get(default="").strip()
            print(f"🟩 [DEBUG] Extracted job title: '{title}'")

            if not any(word.lower() in title.lower() for word in self.exclude_words):
                try:
                    onclick = job_a.attrib.get("onclick", "")
                    match = re.search(r"enavOpenNew\('(.+?)'\)", onclick)
                    job_link = match.group(1) if match else job_a.attrib.get("href", "")
                    full_url = response.urljoin(job_link)

                    last_seen = job.css("a.lk.lastseen::text").get(default="").strip().lower()

                    if "2 days ago" in last_seen:
                        print(f"🛑 [STOP] Found '2 days ago' posting. Stopping crawl after this page.")
                        self.stop_crawling = True
                        break

                    print(f"✅ [MATCH] Yielding job: '{title}'")
                    yield {
                        "title": title,
                        "href": full_url
                    }
                except Exception as e:
                    print(f"❌ [ERROR] Exception for job '{title}': {e}")
        
        if not self.stop_crawling:
            next_page = response.css("a#pager-next::attr(href)").get()
            if next_page:
                self.page_num += 1
                next_url = response.urljoin(next_page)
                print(f"➡️ [DEBUG] Following next page: {next_url}")
                yield response.follow(next_page, callback=self.parse)
            else:
                print(f"🚫 [INFO] No 'Next' page found. Ending crawl.")
        else:
            print(f"🛑 [INFO] Crawling stopped by date filter.")
