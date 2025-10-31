from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_WORD_LIMIT = 100 
DEFAULT_DELAY = 5 #this seems to be in-built into the code 

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    if resp.status != 200 or resp.raw_response is None:
        return []
    html_content = None
    try:
        raw_bytes = resp.raw_response.content
        if isinstance(raw_bytes, bytes):
            html_content = raw_bytes.decode('utf-8', errors='ignore')
        else:
            html_content = str(raw_bytes)
    except Exception as e:
        print(f"Error accessing or decoding raw content for {url}: {e}")
        return []
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        links = set()
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            absolute_url = urljoin(url, href)
            parsed_url = urlparse(absolute_url)
            cleaned_url = parsed_url._replace(fragment='').geturl()
            if is_valid_size(html_content) and is_valid(cleaned_url):
                links.add(cleaned_url)
        return list(links)
    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}")
        return []
    
def is_valid_size(html_content):
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    text = soup.get_text()
    if len(text.split()) < MIN_WORD_LIMIT:
        return False
    return True 

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        allowed_domains = {".ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
        domain = parsed.netloc.lower()
        valid = any(domain.endswith(allowed) for allowed in allowed_domains)
        if not valid:
            return False

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        #TODO: add the r'(calender|event|...
       
        if re.search(r'(calender|event|\d{4}-\d{2}-\d{2})', parsed.path.lower()):
            return False

        parts_path = [i for i in parsed.path.split('/') if i]
        if len(parts_path) > 5 or len(url) > 100:
            return False

        if 'download' in parsed.path or 'attachment' in parsed.path:
            return False

    except Exception as e:
        print(f"Error accessing or decoding raw content for {url}: {e}")
        return False
    
    return True

