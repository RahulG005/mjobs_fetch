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

class bmoSpider(scrapy.Spider):
    name = "bmo"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_words = load_exclude_words()
        self.page_limit = 3  # fetch 3 pages max
        self.jobs_per_page = 20
        self.filtered_by_date = 0
        self.filtered_by_exclude = 0
        self.yielded = 0


    def start_requests(self):
        base_url = "https://bmo.wd3.myworkdayjobs.com/wday/cxs/bmo/External/jobs"
        for page in range(self.page_limit):
            offset = page * self.jobs_per_page
            body = {
                "appliedFacets": {
                    "Country": ["a30a87ed25634629aa6c3958aa2b91ea"],
                    "timeType": ["027a38bd0f0901102412b6de9c095800"]
                },
                "limit": self.jobs_per_page,
                "offset": offset,
                "searchText": ""
            }
        

            yield scrapy.Request(
                url=base_url,
                method="POST",
                body=json.dumps(body),
                headers={'Content-Type': 'application/json',
                        "Accept": "application/json",
                        "User-Agent": "your-postman-user-agent",
                        "Origin": "https://bmo.wd3.myworkdayjobs.com"
                        },
                callback=self.parse,
                meta={'page': page}
            )

    def parse(self, response):
        data = json.loads(response.text)
        jobs = data.get('jobPostings', [])

        print(f"📥 Page {response.meta['page'] + 1}: Total jobs fetched: {len(jobs)}")

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        for job in jobs:
            title = job.get('title', '').lower()
            posted_on = job.get('postedOn', '').lower()
            external_path = job.get('externalPath', '')

            job_slug = external_path.split('/')[-1]
            apply_url = f"https://bmo.wd3.myworkdayjobs.com/en-US/External/job/{job_slug}"

            if 'yesterday' not in posted_on and 'today' not in posted_on:
                self.filtered_by_date += 1
                continue

            if any(ex_word in title for ex_word in self.exclude_words):
                self.filtered_by_exclude += 1
                continue

            self.yielded += 1
            yield {
                'title': job.get('title'),
                'applyUrl': apply_url,
                'postedOn': job.get('postedOn'),
            }

        if response.meta.get('page') == self.page_limit - 1:
            print("📊 Final Filtering Summary:")
            print(f"  ➤ Filtered out by date: {self.filtered_by_date}")
            print(f"  ➤ Filtered out by exclude_words: {self.filtered_by_exclude}")
            print(f"  ✅ Jobs remaining after filtering: {self.yielded}")