from time import sleep
import os
from datetime import datetime

from selenium import webdriver


class AutomationStep():
    def __init__(self, function, name, wait_after_in_sec, in_headless, is_headless):
        self.function = function
        self.name = name
        self.wait_after_in_sec = wait_after_in_sec
        self.in_headless = in_headless
        self.is_headless = is_headless
        
    def run(self, workspace, browser, log_file):
        if self.__should_run():
            self.log_step(log_file, self._name)
            self.function(workspace, browser)
            sleep(self.wait_after_in_sec)

    def log_step(self, log_file, name):
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"{date}: [INFO] {self.name}\n")
        print(f"[INFO] {self.name}")

    def __should_run(self):
        return (not self.is_headless) or (self.is_headless and self.in_headless)


class BrowserAutomation():
    def __init__(self, args, initial_page, resolution, log_dir, log_name):
        self.headless = args.headless_mode
        self.__browser = self.__setup_chrome_browser(args.executor, args.headless_mode, resolution)
        self.__enter_initial_page(initial_page)
        self.__steps = []
        self.__workspace = {'args': args}
        self.__log_file = self.__get_logger_file(log_dir, log_name)

    def __del__(self):
        if self.headless:
            self.__browser.quit()
        self.__log_file.close()
    
    def __setup_chrome_browser(self, command_executor_, headless, resolution):
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--window-size={resolution[0]},{resolution[1]}")
        self.driver = webdriver.Remote(command_executor=command_executor_, options=chrome_options)
        return self.driver

    def __enter_initial_page(self, initial_page_url):
        print(f"Entering initial page: {initial_page_url}")
        self.__browser.get(initial_page_url)
        sleep(2)
        
    def add_step(self, function, name, wait_after_in_sec, in_headless):
        self.__steps.append(AutomationStep(function, name, wait_after_in_sec, in_headless, self.headless))
        
    def perform_all_steps(self):
        for step in self.__steps:
            step.run(self.__workspace, self.__browser, self.__log_file)
            
    def save_screenshot(self, filename):
        self.driver.save_screenshot(f"{filename}.png")

    def __get_logger_file(self, log_dir, file_name):
        date = datetime.now().strftime('%Y_%m_%d_%H_%M')
        file_name = f"{date}_{file_name}"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, file_name)
        return open(log_path, 'w')
