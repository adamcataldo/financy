from collections import namedtuple
from executor import RetryingExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import logging


def extract_amount(ba_str):
    return float(ba_str.split(" ")[0].replace("$", "").replace(",", ""))


class Liquidity:
    def __init__(self):
        self.executor = RetryingExecutor(1000)

    def __enter__(self):
        chrome_opts = Options()
        chrome_opts.headless = True
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        chrome_opts.add_argument(f"user-agent={user_agent}")
        self.browser = webdriver.Chrome(options=chrome_opts)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()

    def open_browser(self):
        self.__enter__()

    def close_browser(self):
        self.__exit__()

    def bid_ask(self, symbol):
        logging.info(f"fetching bid/ask for {symbol}")
        return self.executor.execute(lambda: self.__bid_ask_exec(symbol))

    def __bid_ask_exec(self, symbol):
        try:
            symbol = symbol.replace(".", "%2F")
            self.browser.get(f"https://digital.fidelity.com/prgw/digital/research/quote/dashboard/summary?symbol={symbol}")
            ask_path = "//div[@nre-cy='nre-quick-quote-ask-size-value']"
            bid_path = "//div[@nre-cy='nre-quick-quote-bid-size-value']"
            delay = 3
            WebDriverWait(self.browser, delay).until(ec.presence_of_element_located((By.XPATH, ask_path)))
            bid_str = self.browser.find_element(By.XPATH, bid_path).text
            ask_str = self.browser.find_element(By.XPATH, ask_path).text
            bid = extract_amount(bid_str)
            ask = extract_amount(ask_str)
            BidAsk = namedtuple('BidAsk', field_names=['bid', 'ask'])
            return BidAsk(bid, ask)
        except Exception as err:
            logging.error(f"Unexpected {err=} on {symbol}, {type(err)=}")
            return None
