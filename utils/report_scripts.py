import re
from urllib.parse import urlparse
from io import StringIO
from collections import defaultdict

def count_unique_pages_from_log(log_content):
    unique_urls = set()
    
    log_file = StringIO(log_content)

    for line in log_file:
        line = line.strip()
        
        if "Downloaded" in line and ", status <" in line:
            try:
                _, url_and_rest = line.split("Downloaded", 1)
                url_and_rest = url_and_rest.strip()
                
                full_url, _ = url_and_rest.split(", status <", 1)
                
                full_url = full_url.strip()
                
                if not full_url:
                    continue

                parsed = urlparse(full_url)
                url_without_fragment = parsed._replace(fragment='').geturl()
                unique_urls.add(url_without_fragment)
            
            except ValueError as e:
                print(f"Skipping malformed log line or URL: {line} due to: {e}")
                continue

    return len(unique_urls), unique_urls

def analyze_subdomains(unique_urls):
    subdomain_freq = defaultdict(int)
    
    for url in unique_urls:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        
        if netloc.endswith('.uci.edu') or netloc == 'uci.edu':
            subdomain_freq[netloc] += 1
            
    return dict(subdomain_freq)

with open('Logs/Worker.log', 'r') as f:
    log_data = f.read()

count, unique_urls_set = count_unique_pages_from_log(log_data)

print(f"Total Unique Pages Found (excluding fragment): {count}")

subdomain_data = analyze_subdomains(unique_urls_set)

print(f"Found {len(subdomain_data)} unique subdomains under uci.edu.")

print("\nSubdomain Report:")
for subdomain in sorted(subdomain_data.keys()):
    page_count = subdomain_data[subdomain]
    print(f"{subdomain}, {page_count}")
