#!/usr/bin/env python3

from time import sleep
import os
import re
import signal
import sys

from browsing_automations import BrowserAutomation

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------- #
#                                Script settings                               #
# ---------------------------------------------------------------------------- #

HEADLESS = True
COMMAND_EXECUTOR = 'http://192.168.1.131:3000/webdriver'

TRENING = "Trening.Obwodowy"
TRENER = "Małgorzata.Olejniczak"

ZDROFIT_SITE = 'https://zdrofit.pl/#logowanie'
ALCHEMIA_GYM_SCHEDULE_SITE = 'https://zdrofit.pl/kluby-fitness/gdansk-alchemia/grafik-zajec'

email = "dominik.trochowski@gmail.com"
SCRIPT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
PASSWD_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, os.pardir, "passwd_zdrofit")

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                    Helpers                                   #
# ---------------------------------------------------------------------------- #

def timeout_handler(signum, frame):
    print("TIMEOUT occurred!")
    raise Exception("TIMEOUT - while searching for training")


def get_passwd():
    with open(PASSWD_FILE_PATH, 'r') as passwd_file:
        return passwd_file.read()


def save_screen(browser, file_name):
    browser.save_screenshot(f"{file_name}.png")
    

def get_search_pattern(trening, trener):
    return re.compile(''.join(['\>(', trening, ').*(', trener, ').*id=\"([a-z][0-9]{6})\"']))


def find_training_id(browser, trening, trener):
    training_descrićption = re.search(get_search_pattern(trening, trener), browser.page_source)
    return re.findall('id=\"([a-z][0-9]{6})\"', training_descrićption.group(0))[0]


def try_to_click(browser, training_id):
    try:
        browser.find_element(By.ID, training_id).click()
    except:
        return False
    else:
        return True


def get_into_training_signing(browser, training_id):
    FUNCTION_TIMEOUT = 20 # s
    SCROLL_ITER_PX = 500 # px
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(FUNCTION_TIMEOUT)

    y_pos = 200
    x_pos = 0

    while (not try_to_click(browser, training_id)):
        browser.execute_script(f"window.scrollTo({x_pos}, {y_pos})")
        y_pos += SCROLL_ITER_PX
        sleep(0.2)

    signal.alarm(0)

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                               Automation Steps                               #
# ---------------------------------------------------------------------------- #

def accept_cookies(workspace, browser):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button'))).click()


def enter_credentials(workspace, browser):
    browser.find_element(By.ID, 'member_login_form_email').send_keys(email)
    browser.find_element(By.ID, 'member_login_form_password').send_keys(get_passwd())
    browser.find_element(By.ID, 'member_login_form_submit').click()


def jump_to_gym_schedule(workspace, browser):
    browser.get(ALCHEMIA_GYM_SCHEDULE_SITE)


def find_right_trenning(workspace, browser):
    training_id = find_training_id(browser, TRENING, TRENER)
    workspace["training_id"] = training_id


def click_on_chosen_training(workspace, browser):
    try:
        get_into_training_signing(browser, workspace["training_id"])
    except Exception as e:
        print(e)
        sys.exit(-1)
        

def training_sign_up(workspace, browser):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'schedule_register_form_submit'))).click()

# ---------------------------------------------------------------------------- #

if __name__ == "__main__":
    automation = BrowserAutomation(COMMAND_EXECUTOR, ZDROFIT_SITE, HEADLESS)
    
    automation.add_step(accept_cookies, "Accept cookies", wait_after_in_sec=1.5, in_headless=False)
    automation.add_step(enter_credentials, "Enter credentials", wait_after_in_sec=1, in_headless=True)
    automation.add_step(jump_to_gym_schedule, "Jump to gym schedule", wait_after_in_sec=1, in_headless=True)
    automation.add_step(find_right_trenning, "Find the right training", wait_after_in_sec=0, in_headless=True)
    automation.add_step(click_on_chosen_training, "Click on chosen training", wait_after_in_sec=1.5, in_headless=True)
    automation.add_step(training_sign_up, "Sign up for training", wait_after_in_sec=1.5, in_headless=True)

    automation.perform_all_steps()

    del automation
