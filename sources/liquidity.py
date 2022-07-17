from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

def extract_amount(ba_str):
    return float(ba_str.split(" ")[0].replace("$", "").replace(",", ""))

def bid_ask(symbol):
    chrome_opts = Options()
    chrome_opts.headless = True
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    chrome_opts.add_argument(f"user-agent={user_agent}")
    browser = webdriver.Chrome(options=chrome_opts)
    browser.get("https://digital.fidelity.com/prgw/digital/research/quote/dashboard/summary?symbol=GOOG")
    ask_path = "//div[@nre-cy='nre-quick-quote-ask-size-value']"
    bid_path = "//div[@nre-cy='nre-quick-quote-bid-size-value']"
    delay = 3
    WebDriverWait(browser, delay).until(ec.presence_of_element_located((By.XPATH, ask_path)))
    bid_str = browser.find_element(By.XPATH, bid_path).text
    ask_str = browser.find_element(By.XPATH, ask_path).text
    browser.close()
    bid = extract_amount(bid_str)
    ask = extract_amount(ask_str)
    BidAsk = namedtuple('BidAsk', field_names=['bid', 'ask'])
    return BidAsk(bid, ask)
