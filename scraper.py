from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
#from urllib.robotparser import RobotFileParser

#need to store the robots.txt (can not have multiple requests)
#USING ROBOT.TXT for traps!
#robots_dict = {}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# def extract_next_links(url, resp):
#     if resp.status != 200 or resp.raw_response is None:
#         return []
#     html_content = None
#     try:
#         raw_bytes = resp.raw_response.content
#         if isinstance(raw_bytes, bytes):
#             html_content = raw_bytes.decode('utf-8', errors='ignore')
#         else:
#             html_content = str(raw_bytes)
#     except Exception as e:
#         print(f"Error accessing or decoding raw content for {url}: {e}")
#         return []
#     try:
#         soup = BeautifulSoup(html_content, 'lxml')
#         links = set()
#         for link_tag in soup.find_all('a', href=True):
#             href = link_tag.get('href')
#             absolute_url = urljoin(url, href)
#             parsed_url = urlparse(absolute_url)
#             cleaned_url = parsed_url._replace(fragment='').geturl()
#             links.add(cleaned_url)
#         return list(links)
#     except Exception as e:
#         print(f"Error parsing HTML for {url}: {e}")
#         return []


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
            if is_valid(cleaned_url):
                links.add(cleaned_url)
        return list(links)
    except Exception as e:
        print(f"Error parsing HTML for {url}: {e}")
        return []
def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    #TODO: Detect and avoid sets of similar pages with no information:
        #chccking for near duplicates/exact duplicate:
            #checksums/ page fingerprints (simhash)

        #exact duplicates: use hashes - import hashlib and see if content is same
        #near duplicate: create a fingerprint and check
    #if all coming from same origin - all they have is just nhumbers - clear  bad content - dont crawl this. detect werirdf patterns of urls. go manulaly check. and see if its good or bad content.

    #TODO:dont need domain checking do i - bc it starts from the list of domains listed?  yes check for them. only crawl from them.
    #TODO: do i add the robots.txt thing or is it alr handled
   
    try:
        parsed = urlparse(url)
       
        if parsed.scheme not in set(["http", "https"]):
            return False

        allowed_domains = {".ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}

        domain = parsed.netloc #TODO: do i need to put .lower()
        #netloc is the domain name so i want to parse that
        #TODO: is it case sensitive - irl the uppercase and lowercase dont matter

        valid = False
        for allowed in allowed_domains: #go thru the domains
            if (domain.endswith(allowed)):
                valid = True
                break
        if not valid:
            return False

        #check for calender trap (infinte) #check for infinite redirecting #check for long urls, repeating paths,

         #robot.txt is appended at the end of the url  (placed usually at the root)
        #logic for this:  (robots.txt will either return a allow or disallow and based on thar we can determine if it is valid or not)
            #create the robots.txt url - it just adds to the exisiting url (.../robots.txt)
            #need to make sure you are not caching again - thats why we have the robot_dict to keep track of the urls that have been fetched
            #then acc fetch

        #getting the base url (to attach the robots.txt to b/c its not in that format right now)
        # base_url = f"{parsed.scheme}://{parsed.netloc}"
        # #rp = RobotFileParser()
        # robots_url = f"{base_url}/robots.txt"

        # if robots_url not in robots_dict:
        #     rp = RobotFileParser()
        #     rp.set_url(robots_url)
        #     try:
        #         rp.read()
        #         robots_dict[robots_url] = rp #saves it in the dictionary too
        #     except Exception as e:
        #         print(e)
        #         robots_dict[robots_url] = None

        # #need to check if its allowed/disallowed:
        # if robots_dict[robots_url] is not None:
        #     if not robots_dict[robots_url].can_fetch('*', url):
        #         return False
            # if robots_dict[robots_url].can_fetch('*', url):
            #     return True
            # else:
            #     return False

       
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())


        #TODO: add the r'(calender|event|...
       
        if re.search(r'(calender|event|\d{4}-\d{2}-\d{2})', parsed.path.lower()):
            return False
        #this blocks the year/month trap b/c with the year/month -
        #it generates an unlimited amount of pages with inifinte years and each month - so once it sees this format then it gets blocked


        #checking for infinte redirecting (a to b, b to c, c to d, ...)
        #keep track of how many times a url has been visited (not more than 5 times?)

        parts_path = []

        for i in parsed.path.split('/'):
            if i:
                parts_path.append(i)
               
        if len(parts_path) > 5:
            return False

        if len(url) > 100:
            return False

        #dont crawl any 'downloads' or 'attachmernts' in rhe path
        if 'download' in parsed.path() or 'attachment' in parsed.path():
            return False
       
        return True #or do i just do the above checks before the big return statement

    except TypeError:
        print ("TypeError for ", parsed)
        raise