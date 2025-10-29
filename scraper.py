from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests

MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_WORD_LIMIT = 20000000 
DEFAULT_DELAY = 5

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
            links.add(cleaned_url)
        return list(links)
    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}") 
        return []

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # try:
    #     parsed = urlparse(url)
    #     if parsed.scheme not in set(["http", "https"]):
    #         return False
    #     return not re.match(
    #         r".*\.(css|js|bmp|gif|jpe?g|ico"
    #         + r"|png|tiff?|mid|mp2|mp3|mp4"
    #         + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
    #         + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
    #         + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
    #         + r"|epub|dll|cnf|tgz|sha1"
    #         + r"|thmx|mso|arff|rtf|jar|csv"
    #         + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    # except TypeError:
    #     print ("TypeError for ", parsed)
    #     #raise --> she wrote raise here, don't know what to do with it
    
    try:
        metadata = requests.head(url)

        content_type = metadata.headers.get("Content-Type")
        content_size = metadata.headers.get("Content-Length") #check for large size
        if 'text/html' not in content_type: #indicates NOT web page
            return False 
        if content_size and int(content_size) > MAX_FILE_SIZE:
            return False
        
        response = requests.get(url)
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        if  not (200 <= response.status_code <= 300):
            return False

        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text()
        if len(text.split()) < MIN_WORD_LIMIT: #check for valid info 
            return False

    except Exception as e:
        print(f"Error accessing or decoding raw content for {url}: {e}")
        return False
    
    return True




def get_delay(url, user_agent='*'):
    domain = urlparse(url).netloc
    robots_url = f'https://{domain}/robots.txt'
    response = requests.get(robots_url)
    delay = None
    if  (200 <= response.status_code < 300):
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        delay = rp.crawl_delay(user_agent)
    return delay or DEFAULT_DELAY

print(is_valid("https://www.cnn.com/2025/10/29/politics/maduro-cyberattack-tr"))