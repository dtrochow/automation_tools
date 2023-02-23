#!/usr/bin/env python3

import time
import os
import re
import signal
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains

# ---------------------------------------------------------------------------- #
#                                Script settings                               #
# ---------------------------------------------------------------------------- #

SCRIPT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

COMMAND_EXECUTOR = '127.0.0.1:9515'
ZDROFIT_SITE = 'https://zdrofit.pl/#logowanie'
ALCHEMIA_GYM_SCHEDULE_SITE = 'https://zdrofit.pl/kluby-fitness/gdansk-alchemia/grafik-zajec'

HEADLESS = True

TRENING = "Salsation"
TRENER = "Dorota.Turzańska-Skiba"

email = "dominik.trochowski@gmail.com"
PASSWD_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, os.pardir, "passwd_zdrofit")

# ---------------------------------------------------------------------------- #

def get_passwd():
    with open(PASSWD_FILE_PATH, 'r') as passwd_file:
        return passwd_file.read()


def setup_browser(headless=False):
    '''
    Local Chromium Driver can be downaloaded from:
    https://chromedriver.storage.googleapis.com/index.html?path=110.0.5481.77/
    '''
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
    return webdriver.Remote(command_executor=COMMAND_EXECUTOR, options=chrome_options)


def save_screen(browser, file_name):
    browser.save_screenshot(f"{file_name}.png")
    

def get_search_pattern(trening, trener):
    return re.compile(''.join(['\>(', trening, ').*(', trener, ').*id=\"([a-z][0-9]{6})\"']))


def find_training_id(browser, trening, trener):
    training_descrićption = re.search(get_search_pattern(trening, trener), browser.page_source)
    return re.findall('id=\"([a-z][0-9]{6})\"', training_descrićption.group(0))[0]


def timeout_handler(signum, frame):
    print("TIMEOUR occured!")
    raise Exception("TIMEOUT - while searching for training")


def try_to_click(browser, training_id):
    try:
        browser.find_element(By.ID, training_id).click()
    except:
        return False
    else:
        return True


def get_into_training_signing(browser, training_id):
    FUNCTION_TIMEOUT = 20 # s
    SCROLL_PX_ITER = 500 # px
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(FUNCTION_TIMEOUT)

    y_pos = 200
    x_pos = 0

    while (not try_to_click(browser, training_id)):
        browser.execute_script(f"window.scrollTo({x_pos}, {y_pos})")
        y_pos += SCROLL_PX_ITER
        time.sleep(0.2)

    signal.alarm(0)


def scrap():
    browser = setup_browser(HEADLESS)

    print("[1] Open login page")
    browser.get(ZDROFIT_SITE)
    time.sleep(2)

    print("[2] Accept cookies")
    if not HEADLESS:
        WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button'))).click()
        time.sleep(2)

    print("[3] Enter credentials")
    browser.find_element(By.ID, 'member_login_form_email').send_keys(email)
    browser.find_element(By.ID, 'member_login_form_password').send_keys(get_passwd())
    browser.find_element(By.ID, 'member_login_form_submit').click()
    time.sleep(1)

    print("[4] Jump to gym schedule")
    browser.get(ALCHEMIA_GYM_SCHEDULE_SITE)
    time.sleep(1)

    print("[5] Find the right training")
    training_id = find_training_id(browser, TRENING, TRENER)
    time.sleep(1)

    print("[6] Click on chosen training")
    try:
        get_into_training_signing(browser, training_id)
    except Exception as e:
        print(e)
        sys.exit(-1)
    time.sleep(1)

    print("[7] Sign up for training")
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'schedule_register_form_submit'))).click()
    time.sleep(2)
    
    if HEADLESS:
        browser.quit()


if __name__ == "__main__":
    scrap()
