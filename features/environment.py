"""
Environment for Behave Testing
"""
from os import getenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

WAIT_SECONDS = int(getenv('WAIT_SECONDS', '45'))
BASE_URL = getenv('BASE_URL', 'http://localhost:8081')
DRIVER = getenv('DRIVER', 'chrome').lower()

# features/environment.py
#from selenium import webdriver

def before_all(context):
    """ Executed once before all tests """
    context.base_url = BASE_URL
    context.wait_seconds = WAIT_SECONDS
    options = webdriver.ChromeOptions()
    options.unhandled_prompt_behavior = 'accept'
    options.add_argument("--no-first-run")
    options.add_argument("--enable-automation")
    options.add_argument("--disable-extensions")
    options.add_argument("--enable-logging=stderr")
    options.add_argument("--log-level=2")
    options.add_argument("--disable-component-update")
    options.add_argument("--enable-crash-reporter-for-testing")
    options.add_argument("--disable-features=OptimizationHints")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("start-maximized")
    context.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=options)   
    context.driver.implicitly_wait(context.wait_seconds)
    context.config.setup_logging()
    context.driver.get(context.base_url)


def after_all(context):
    """ Executed after all tests """
    context.driver.quit()
    
