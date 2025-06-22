import subprocess

spiders = [
    'td',
    'cibc',
    'eluta',
    'rbc',
    'manulife',
    'scotiabank',
    'sunlife',
    'bmo'
]

output_file = 'output.json'

for spider in spiders:
    print(f"Running spider: {spider}")
    result = subprocess.run(
        ['scrapy', 'crawl', spider, '-o', output_file],
        capture_output=False  # Set to True if you want to capture output in Python
    )
    print(f"Finished spider: {spider} (exit code: {result.returncode})\n")
