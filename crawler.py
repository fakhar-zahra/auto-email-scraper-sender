import requests, re, time, tldextract
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ua = UserAgent()
TIMEOUT = 10
KEY_PATHS = ['/contact', '/about', '/privacy', '/support', '/team']
PRIORITY_EMAIL_PREFIXES = ['info', 'support', 'contact', 'hello', 'admin', 'sales']

def get_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def get_html(url):
    try:
        print(f"🔎 Trying HTML: {url}")
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=TIMEOUT)
        if res.status_code == 200:
            return res.text
    except Exception as e:
        print(f"❌ Request failed for {url}: {e}")
    return None

def get_html_selenium(url):
    try:
        print(f"🧠 Selenium parsing: {url}")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"❌ Selenium failed for {url}: {e}")
        return None

# ✅ Updated extract_emails with email cleaning
def extract_emails(text):
    soup = BeautifulSoup(text, 'html.parser')

    # Remove script, style, and img tags
    for tag in soup(['script', 'style', 'img', 'svg', 'noscript']):
        tag.decompose()

    visible_text = soup.get_text(separator=' ', strip=True)

    raw_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", visible_text)
    
    # 🧼 Clean emails: remove trailing dots or commas
    cleaned_emails = set()
    for e in raw_emails:
        cleaned = e.strip().strip('.').strip(',').lower()
        if not cleaned.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            cleaned_emails.add(cleaned)
    
    return cleaned_emails

def filter_priority_emails(emails, domain):
    result = set()
    for email in emails:
        local, _, host = email.partition('@')
        if domain in host and any(local.startswith(p) for p in PRIORITY_EMAIL_PREFIXES):
            result.add(email)
    return result or emails

def crawl_with_priority_paths(base_url):
    visited = set()
    all_emails = set()
    domain = get_domain(base_url)

    for path in KEY_PATHS:
        full_url = urljoin(base_url, path)
        if full_url in visited:
            continue
        visited.add(full_url)

        html = get_html(full_url)
        if html:
            emails = extract_emails(html)
            all_emails.update(emails)
            if emails:
                break
    return filter_priority_emails(all_emails, domain)

def fallback_html_parse(base_url):
    html = get_html(base_url)
    if html:
        return extract_emails(html)
    return set()

def fallback_selenium_parse(base_url):
    html = get_html_selenium(base_url)
    if html:
        return extract_emails(html)
    return set()

def crawl_site(base_url):
    base_url = base_url.strip()
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    print(f"🌐 Crawling: {base_url}")
    domain = get_domain(base_url)

    emails = crawl_with_priority_paths(base_url)
    if emails:
        print("✅ Found via priority path")
        return list(emails)

    emails = fallback_html_parse(base_url)
    if emails:
        print("✅ Found via homepage")
        return list(filter_priority_emails(emails, domain))

    emails = fallback_selenium_parse(base_url)
    if emails:
        print("✅ Found via Selenium")
        return list(filter_priority_emails(emails, domain))

    print("❌ No emails found for:", base_url)
    return []

# Optional test
if __name__ == "__main__":
    urls = [
        "https://example.com",
        "https://anotherexample.org",
        "wix.com",
        "https://www.weebly.com",
        "square.site"
    ]
    for url in urls:
        emails = crawl_site(url)
        print("📧 Emails:", emails)
