"""
Environment for Behave Testing
"""
from os import getenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(ChromeDriverManager().install()) 

WAIT_SECONDS = int(getenv('WAIT_SECONDS', '30'))
BASE_URL = getenv('BASE_URL', 'http://localhost:8081')
DRIVER = getenv('DRIVER', 'chrome').lower()

# features/environment.py
#from selenium import webdriver

def before_all(context):
    """ Executed once before all tests """
    context.base_url = BASE_URL
    context.wait_seconds = WAIT_SECONDS
    context.driver = driver    
    context.driver.implicitly_wait(context.wait_seconds)
    context.config.setup_logging()


def after_all(context):
    """ Executed after all tests """
    context.driver.quit()
    
