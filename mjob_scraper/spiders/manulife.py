import scrapy
import json
import os
from datetime import datetime, timedelta

def load_exclude_words(filename="exclude_words.txt"):
    # Get the absolute path to project root (two levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

class ManulifeSpider(scrapy.Spider):
    name = "manulife"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()
    
    def start_requests(self):
        url = "https://careers.manulife.com/widgets"
        body = {
            "sortBy": "Most recent",
            "subsearch": "",
            "from": 0,
            "jobs": True,
            "counts": True,
            "all_fields": ["category", "country", "state", "city", "type", "phLocSlider"],
            "clearAll": False,
            "country": "global",
            "ddoKey": "eagerLoadRefineSearch",
            "deviceType": "mobile",
            "global": True,
            "isSliderEnable": True,
            "jdsource": "facets",
            "keywords": "",
            "lang": "en_global",
            "locationData": {
                "sliderRadius": 50,
                "aboveMaxRadius": True,
                "LocationUnit": "miles"
            },
            "pageId": "page9",
            "pageName": "search-results",
            "refNum": "MFZMFIUS",
            "s": "1",
            "selected_fields": {
                "country": ["Canada"]
            },
            "siteType": "external",
            "size": 50,
            "sort": {
                "order": "desc",
                "field": "postedDate"
            }
        }

        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://careers.manulife.com",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "Referer": "https://careers.manulife.com/global/en/search-results"
        }
        
        yield scrapy.Request(
            url=url,
            method="POST",
            body=json.dumps(body),
            headers=headers,
            callback=self.parse
        )
        
    def parse(self, response):
           
        try:
            data = json.loads(response.text)
            jobs = data.get('eagerLoadRefineSearch', {}).get('data', {}).get('jobs', [])
        except Exception as e:
            self.logger.error(f"❌ Error parsing response: {e}")
            return

        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        filtered_by_date = 0
        filtered_by_exclude = 0
        yielded = 0

        for job in jobs:
            title = job.get('title', '').lower()
            apply_url = job.get('applyUrl', '')
            posted_date_str = job.get('postedDate', '')[:10]

            try:
                posted_date = datetime.strptime(posted_date_str, '%Y-%m-%d').date()
            except Exception:
                continue

            if posted_date not in (today, yesterday):
                filtered_by_date += 1
                continue

            if any(ex_word in title for ex_word in self.exclude_words):
                filtered_by_exclude += 1
                continue

            yielded += 1
            yield {
                "title": job.get("title"),
                "applyUrl": apply_url
            }

        self.logger.info("📊 Summary:")
        self.logger.info(f"  ➤ Total jobs found: {len(jobs)}")
        self.logger.info(f"  ➤ Filtered out by date: {filtered_by_date}")
        self.logger.info(f"  ➤ Filtered out by exclude_words: {filtered_by_exclude}")
        self.logger.info(f"  ✅ Jobs yielded: {yielded}")
        
        