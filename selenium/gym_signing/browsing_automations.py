from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By


class AutomationStep():
    def __init__(self, function, name, wait_after_in_sec, in_headless, is_headless):
        self.function = function
        self.name = name
        self.wait_after_in_sec = wait_after_in_sec
        self.in_headless = in_headless
        self.is_headless = is_headless
        
    def run(self, workspace, browser):
        if self.__should_run():
            print(f"[INFO] {self.name}")
            self.function(workspace, browser)
            sleep(self.wait_after_in_sec)
            
    def __should_run(self):
        return (not self.is_headless) or (self.is_headless and self.in_headless)


class BrowserAutomation():
    def __init__(self, args, initial_page):
        self.headless = args.headless_mode
        self.__browser = self.__setup_chrome_browser(args.executor, args.headless_mode)
        self.__enter_initial_page(initial_page)
        self.__steps = []
        self.__workspace = {'args': args}
    
    def __del__(self):
        if self.headless:
            self.__browser.quit()
    
    def __setup_chrome_browser(self, command_executor_, headless):
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
        return webdriver.Remote(command_executor=command_executor_, options=chrome_options)
    
    def __enter_initial_page(self, initial_page_url):
        print(f"Entering initial page: {initial_page_url}")
        self.__browser.get(initial_page_url)
        sleep(2)
        
    def add_step(self, function, name, wait_after_in_sec, in_headless):
        self.__steps.append(AutomationStep(function, name, wait_after_in_sec, in_headless, self.headless))
        
    def perform_all_steps(self):
        for step in self.__steps:
            step.run(self.__workspace, self.__browser)
