import subprocess

spiders = [
    'td',
    'cibc',
    'eluta'
]

output_file = 'output.json'  # or 'output.jsonl' for JSON Lines format

for spider in spiders:
    print(f"Running spider: {spider}")
    # Use -o for append mode; change to -O for overwrite
    result = subprocess.run(
        ['scrapy', 'crawl', spider, '-o', output_file],
        capture_output=False  # Set to True if you want to capture output in Python
    )
    print(f"Finished spider: {spider} (exit code: {result.returncode})\n")
