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

class sunlifeSpider(scrapy.Spider):
    name = "sunlife"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()

    def start_requests(self):
        url = "https://sunlife.wd3.myworkdayjobs.com/wday/cxs/sunlife/Experienced-Jobs/jobs"  
        body = {
            "appliedFacets": {
                "Location_Country": ["a30a87ed25634629aa6c3958aa2b91ea"]
            },
            "limit": 20,
            "offset": 0,
            "searchText": ""
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
        jobs = data.get('jobPostings', [])

        print(f"📥 Total jobs fetched: {len(jobs)}")
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        filtered_by_date = 0
        filtered_by_exclude = 0
        yielded = 0
        
        for job in jobs:
            title = job.get('title', '').lower()
            posted_on = job.get('postedOn', '').lower()
            external_path = job.get('externalPath', '')
             # Extract job slug (e.g., Change-Specialist_JR00111305)
            job_slug = external_path.split('/')[-1]
        
        # Final apply URL
            apply_url = f"https://sunlife.wd3.myworkdayjobs.com/en-US/Experienced-Jobs/job/{job_slug}"
            
            
            # Filter out jobs not posted today or yesterday
            if 'yesterday' not in posted_on and 'today' not in posted_on:
                filtered_by_date += 1
                continue

            # Filter out jobs containing unwanted words
            if any(ex_word in title for ex_word in self.exclude_words):
                filtered_by_exclude += 1
                continue

            # Yield the cleaned job record
            yielded += 1
            yield {
                'title': job.get('title'),
                'applyUrl': apply_url,
                'postedOn': job.get('postedOn'),
            }

        print("📊 Filtering Summary:")
        print(f"  ➤ Filtered out by date: {filtered_by_date}")
        print(f"  ➤ Filtered out by exclude_words: {filtered_by_exclude}")
        print(f"  ✅ Jobs remaining after filtering: {yielded}")
