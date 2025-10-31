from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen

traps = ["isg.ics.uci.edu/events/*", "*/events/*", ".pdf", "ngs.ics", "eppstein/pix", "archive.ics.uci.edu"] 
from urllib.robotparser import RobotFileParser

MAX_FILE_SIZE = 10^7 #10 megabytes
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
            if is_valid_file_size(url) and is_valid_word_count(html_content) and is_valid(cleaned_url) and not no_follow_meta(soup):
                links.add(cleaned_url)
        return list(links)
    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}")
        return []

def is_valid_file_size(url):
    with urlopen(url) as response:
        content = response.read()
        size = len(content) #size in bytes  
        return size <= MAX_FILE_SIZE
        
def is_valid_word_count(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    text = soup.get_text()
    if len(text.split()) < MIN_WORD_LIMIT:
        return False
    return True 

def no_follow_meta(soup):
    robot = soup.find('meta', attrs={'name': 'robots'})
    if robot and 'nofollow' in robot.get('content', '').lower():
        return robot and 'nofollow' in robot.get('content', '').lower()

def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}

        domain = parsed.netloc.lower() 
        #netloc is the domain name so i want to parse that

        valid = False
        for allowed in allowed_domains: #go thru the domains
            if ((domain.endswith('.' + allowed)) or (domain == allowed)):
                valid = True
                break
        if not valid:
            return False

        if re.search(r'(calendar|event|\d{4}-\d{2}-\d{2})', parsed.path.lower()):
            return False
            
        #this blocks the year/month trap b/c with the year/month -
        #it generates an unlimited amount of pages with inifinte years and each month - so once it sees this format then it gets blocked

        #checking for infinte redirecting (a to b, b to c, c to d, ...)
        #keep track of how many times a url has been visited (not more than 5 times?)

        parts_path = []
        for i in parsed.path.split('/'):
            if i:
                parts_path.append(i)
               
        if len(parts_path) > 5: #change to higher or leave it?
            return False

        if len(url) > 100: #change to higher no. or leave it?
            return False

        #dont crawl any 'downloads' or 'attachmernts' in the path
        if 'download' in parsed.path.lower() or 'attachment' in parsed.path.lower():
            return False

        for i in traps:
            if i in parsed.geturl():
                return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

        return True #or do i just do the above checks before the big return statement

    except TypeError:
        print("TypeError for ", parsed)
        raise
    

