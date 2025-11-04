from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

traps = ["isg.ics.uci.edu/events/*", "doku.php", "*/events/*", ".pdf", "ngs.ics", "eppstein/pix", "archive.ics.uci.edu"] 

MIN_WORD_LIMIT = 100 
DEFAULT_DELAY = 5 #this seems to be in-built into the code 
maximum_words_found = 0
maximum_words_page = None
token_freq = {}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    global maximum_words_found, maximum_words_page
    if resp.status != 200 or resp.raw_response is None:
        return []
    html_content = None
    try:
        raw_bytes = resp.raw_response.content
        if isinstance(raw_bytes, bytes):
            html_content = raw_bytes.decode('utf-8')
        else:
            html_content = str(raw_bytes)
    except Exception as e:
        print(f"Error accessing or decoding raw content for {url}: {e}")
        return []
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        words = word_count(soup)
        if (words < MIN_WORD_LIMIT):
            return []
            
        if words > maximum_words_found:
            maximum_words_found = words
            maximum_words_page = url
        
        tokenizer(url, soup)  #check for function3

        links = set()

        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            absolute_url = urljoin(url, href)
            parsed_url = urlparse(absolute_url)
            cleaned_url = parsed_url._replace(fragment='').geturl()

            if is_valid(cleaned_url) and not no_follow_meta(soup):
                links.add(cleaned_url)
                
        return list(links)
    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}")
        return []

def word_count(soup):
    for script_or_style in soup(['script', 'style', 'noscript', 'meta', 'svg']):
        script_or_style.decompose()
    text = soup.get_text(separator=" ", strip=True)
    tokens = re.findall(r'[a-z0-9]+', text.lower())
    return len(tokens)
    

def no_follow_meta(soup):
    robot = soup.find('meta', attrs={'name': 'robots'})
    if robot and 'nofollow' in robot.get('content', '').lower():
        return robot and 'nofollow' in robot.get('content', '').lower()

def tokenizer(url, soup):
    global token_freq

    raw_text = soup.get_text(separator=" ")

    stop_words = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", 
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", 
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", 
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", 
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", 
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", 
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", 
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", 
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", 
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", 
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", 
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", 
    "you're", "you've", "your", "yours", "yourself", "yourselves"}

    tokens = re.findall(r'[a-z0-9]+', raw_text.lower())

    for token in tokens: 
        if token not in stop_words and len(token) > 1: 
            if token in token_freq:
                token_freq[token] += 1 
            else:
                token_freq[token] = 1

    
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
               
        if len(parts_path) > 10: #change to higher or leave it?
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
    
def crawler_end():
    global token_freq

    sorted_freq = sorted(token_freq.items(), key = lambda item: item[1], reverse = True)
    with open("token2.txt", "w") as f:
        for word, count in sorted_freq:
            f.write(f"{word} - {count}\n")

    with open("50_most_common2.txt", "w") as f1:
        for key, val in sorted_freq[:50]:
            f1.write(f"{key} - {val}\n")
    
    with open("max_words2.txt", "w") as f2:
        f2.write(f"{maximum_words_page} - {maximum_words_found}\n")

