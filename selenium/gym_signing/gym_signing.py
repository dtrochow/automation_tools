#!/usr/bin/env python3
import os
import sys
import re
from argparse import ArgumentParser
from datetime import datetime

from browsing_automations import BrowserAutomation

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

AUTOMATION_TOOLS_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
sys.path.append(AUTOMATION_TOOLS_DIR_PATH)
from signal_bot.signal import SignalCallMeBot

# ---------------------------------------------------------------------------- #
#                                Script settings                               #
# ---------------------------------------------------------------------------- #

SCRIPT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG_DIR_PATH = os.path.join(SCRIPT_DIR_PATH, "logs")

ZDROFIT_SITE = 'https://zdrofit.pl/#logowanie'

DEFAULT_COMMAND_EXECUTOR = 'http://127.0.0.1:9515'

DEFAULT_TRENING = "Trening"
DEFAULT_TRENER = "Trener.Trener"
DEFAULT_GYM_SCHEDULE_SITE = 'https://zdrofit.pl/kluby-fitness/gdansk-alchemia/grafik-zajec'

DEFAULT_EMAIL = "name.surname@gmail.com"
DEFAULT_PASSWD_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, os.pardir, "passwd_zdrofit")


def validate_args(args):
    if ((args.uuid != None) and (args.apikey == None) or
        (args.uuid == None) and (args.apikey != None)):
        raise Exception("--uuid and --apikey can not be specified singly")


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
    parser.add_argument('-st', '--start_time', dest='start_time', action='store',
                        default=None, help='Training start time (e.g. "19:00")')
    parser.add_argument('-et', '--end_time', dest='end_time', action='store',
                        default=None, help='Training end time (e.g. "19:55")')
    parser.add_argument('-id', '--uuid', dest='uuid', action='store',
                        default=None, help='UUID of the Signal communicator (it can also be a phone number e.g. +49 123 456 789)')
    parser.add_argument('-k', '--apikey', dest='apikey', action='store',
                        default=None, help='The apikey that you received during the activation process (Signal CallMeBot)')
    parser.add_argument('-ld', '--log_dir', dest='log_dir', action='store',
                        default=DEFAULT_LOG_DIR_PATH, help='Logs directory')
    
    args = parser.parse_args()
    validate_args(args)
    
    return args

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                    Helpers                                   #
# ---------------------------------------------------------------------------- #

def get_passwd(password_file_path):
    with open(password_file_path, 'r') as passwd_file:
        return passwd_file.read()


def save_screen(browser, file_name):
    browser.save_screenshot(f"{file_name}.png")
    

def get_search_pattern(trening, trener, start_hour, end_hour):
    return re.compile(''.join(['\>(', trening, ')(.*?)(', start_hour, '.-.', end_hour, ')(.*?)(', trener, ')(.*?)id=\"([a-z][0-9]{6})\"']))


def find_training_ids(browser, trening, trener, start_hour, end_hour):
    return re.findall(get_search_pattern(trening, trener, start_hour, end_hour), browser.page_source)

# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                               Automation Steps                               #
# ---------------------------------------------------------------------------- #

def accept_cookies(workspace, browser, log_file):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button'))).click()


def enter_credentials(workspace, browser, log_file):
    browser.find_element(By.ID, 'member_login_form_email').send_keys(workspace['args'].login)
    browser.find_element(By.ID, 'member_login_form_password').send_keys(get_passwd(workspace['args'].password))
    browser.find_element(By.ID, 'member_login_form_submit').click()


def jump_to_gym_schedule(workspace, browser, log_file):
    browser.get(workspace['args'].schedule_site)


def find_right_training(workspace, browser, log_file):
    training_ids = find_training_ids(browser, workspace['args'].training, workspace['args'].trener,
                                   workspace['args'].start_time, workspace['args'].end_time)
    log_file.write(f"Training IDs found:\n")
    for id in training_ids:
        log_file.write(f"ID: {id[-1]}\n")
    workspace["training_ids"] = training_ids


def move_to_training_reservation_page(workspace, browser, log_file):
    training_id = workspace['training_ids'][0][-1][1:]
    log_file.write(f"Chosen training ID: {training_id}\n")
    reservetion_page = f"{DEFAULT_GYM_SCHEDULE_SITE}/{training_id}#rezerwacja"
    browser.get(reservetion_page)


def training_sign_up(workspace, browser, log_file):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'schedule_register_form_submit'))).click()
    log_file.write("You are signed up!\n")

# ---------------------------------------------------------------------------- #

if __name__ == "__main__":
    args = parse_args(ArgumentParser(description='Gym Signing Tool'))
    automation = BrowserAutomation(args, ZDROFIT_SITE, (1920, 1080), args.log_dir, "zdrofit_signing.log")
    
    automation.add_step(accept_cookies, "Accept cookies", wait_after_in_sec=1, in_headless=False)
    automation.add_step(enter_credentials, "Enter credentials", wait_after_in_sec=2.2, in_headless=True)
    automation.add_step(jump_to_gym_schedule, "Jump to gym schedule", wait_after_in_sec=1, in_headless=True)
    automation.add_step(find_right_training, "Find the right training", wait_after_in_sec=0, in_headless=True)
    automation.add_step(move_to_training_reservation_page, "Move to training reservation page", wait_after_in_sec=0.5, in_headless=True)
    automation.add_step(training_sign_up, "Sign up for training", wait_after_in_sec=2, in_headless=True)
    
    automation.perform_all_steps()
    
    if args.uuid:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        training = args.training.replace('.', ' ')
        trener = args.trener.replace('.', ' ')
        SignalCallMeBot(args.uuid, args.apikey).send_message(f"{date} [ZDROFIT]: {args.login} is signed up for a <{training}> training with <{trener}>\nTraining time: {args.start_time}-{args.end_time}")

    del automation
