#!/usr/bin/env python3

from time import sleep
import os
import re
import signal
import sys
from argparse import ArgumentParser

from browsing_automations import BrowserAutomation

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------- #
#                                Script settings                               #
# ---------------------------------------------------------------------------- #

SCRIPT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ZDROFIT_SITE = 'https://zdrofit.pl/#logowanie'

DEFAULT_COMMAND_EXECUTOR = 'http://192.168.1.131:3000/webdriver'

DEFAULT_TRENING = "Trening.Obwodowy"
DEFAULT_TRENER = "Małgorzata.Olejniczak"
DEFAULT_GYM_SCHEDULE_SITE = 'https://zdrofit.pl/kluby-fitness/gdansk-alchemia/grafik-zajec'

DEFAULT_EMAIL = "name.surname@gmail.com"
DEFAULT_PASSWD_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, os.pardir, "passwd_zdrofit")


def parse_args(parser):
    parser.add_argument('-hm', '--headless_mode', action="store_true", help='Enable headless mode')
    parser.add_argument('-e', '--executor', dest='executor', action='store',
                        default=DEFAULT_COMMAND_EXECUTOR, help='Executor URL')
    parser.add_argument('--training', dest='training', action='store',
                        default=DEFAULT_TRENING, help='Trening name (e.g. Trening.Obwodowy). Use "." instead of spaces.')
    parser.add_argument('--trener', dest='trener', action='store',
                        default=DEFAULT_TRENER, help='Trener name (e.g. Małgorzata.Olejniczak). Use "." instead of spaces.')
    parser.add_argument('-s', '--schedule_site', dest='schedule_site', action='store',
                        default=DEFAULT_GYM_SCHEDULE_SITE, help='Trainings schedule site URL')
    parser.add_argument('-l', '--login', dest='login', action='store',
                        default=DEFAULT_EMAIL, help='Login to zdrofit.pl site')
    parser.add_argument('-p', '--password', dest='password', action='store',
                        default=DEFAULT_PASSWD_FILE_PATH, help='Password to zdrofit.pl site')
    
    return parser.parse_args()

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                    Helpers                                   #
# ---------------------------------------------------------------------------- #

def timeout_handler(signum, frame):
    print("TIMEOUT occurred!")
    raise Exception("TIMEOUT - while searching for training")


def get_passwd(password_file_path):
    with open(password_file_path, 'r') as passwd_file:
        return passwd_file.read()


def save_screen(browser, file_name):
    browser.save_screenshot(f"{file_name}.png")
    

def get_search_pattern(trening, trener):
    return re.compile(''.join(['\>(', trening, ').*(', trener, ').*id=\"([a-z][0-9]{6})\"']))


def find_training_id(browser, trening, trener):
    training_description = re.search(get_search_pattern(trening, trener), browser.page_source)
    return re.findall('id=\"([a-z][0-9]{6})\"', training_description.group(0))[0]


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
    browser.find_element(By.ID, 'member_login_form_email').send_keys(workspace['args'].login)
    browser.find_element(By.ID, 'member_login_form_password').send_keys(get_passwd(workspace['args'].password))
    browser.find_element(By.ID, 'member_login_form_submit').click()


def jump_to_gym_schedule(workspace, browser):
    browser.get(workspace['args'].schedule_site)


def find_right_training(workspace, browser):
    training_id = find_training_id(browser, workspace['args'].training, workspace['args'].trener)
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
    args = parse_args(ArgumentParser(description='Setup SSH-Tunnel'))
    automation = BrowserAutomation(args, ZDROFIT_SITE, (1920, 1080))
    
    automation.add_step(accept_cookies, "Accept cookies", wait_after_in_sec=1.5, in_headless=False)
    automation.add_step(enter_credentials, "Enter credentials", wait_after_in_sec=1, in_headless=True)
    automation.add_step(jump_to_gym_schedule, "Jump to gym schedule", wait_after_in_sec=1, in_headless=True)
    automation.add_step(find_right_training, "Find the right training", wait_after_in_sec=0, in_headless=True)
    automation.add_step(click_on_chosen_training, "Click on chosen training", wait_after_in_sec=1.5, in_headless=True)
    automation.add_step(training_sign_up, "Sign up for training", wait_after_in_sec=1.5, in_headless=True)
    
    automation.perform_all_steps()

    del automation
