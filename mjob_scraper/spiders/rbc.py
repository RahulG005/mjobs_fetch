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

class rbcSpider(scrapy.Spider):
    name = "rbc"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()

    def start_requests(self):
        url = "https://jobs.rbc.com/widgets"  
        body = {
            "ddoKey": "refineSearch",
            "deviceType": "desktop",
            "country": "ca",
            "lang": "en_ca",
            "siteType": "external",
            "pageName": "search-results",
            "sort": {"order": "desc", "field": "postedDate"},
            "sortBy": "Most recent",
            "keywords": "canada",
            "selected_fields": {"type": ["Full time"]},
            "jobs": True,
            "from": 0,
            "size": 120
        }

        yield scrapy.Request(
            url,
            method="POST",
            body=json.dumps(body),
            headers={'Content-Type': 'application/json'},
            callback=self.parse
        )

    def parse(self, response):
        data = json.loads(response.text)
        jobs = data.get('refineSearch', {}).get('data', {}).get('jobs', [])

        print(f"📥 Total jobs fetched: {len(jobs)}")
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        filtered_by_date = 0
        filtered_by_exclude = 0
        yielded = 0
        
        for job in jobs:
            title = job.get('title', '').lower()
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
                'title': job.get('title'),
                'applyUrl': job.get('applyUrl'),
            }
        print("📊 Filtering Summary:")
        print(f"  ➤ Filtered out by date: {filtered_by_date}")
        print(f"  ➤ Filtered out by exclude_words: {filtered_by_exclude}")
        print(f"  ✅ Jobs remaining after filtering: {yielded}")
