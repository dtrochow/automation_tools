import requests


class SignalCallMeBot():
    '''
    Allows to send messages to Signal communicator
    docs: https://www.callmebot.com/blog/free-api-signal-send-messages/
    
    param uuid: (string) UUID of the Signal communicator (it can also be a phone number e.g. +49 123 456 789)
    param api_key: (string) The apikey that you received during the activation process (step 4-5 above)
    '''
    SIGNAL_CALLME_BOT_URL = 'https://api.callmebot.com/signal/send.php'
    
    def __init__(self, uuid, api_key):
        self.UUID = uuid
        self.api_key = api_key
        
    def send_message(self, message):
        message.replace(' ', '+')
        url = f"{self.SIGNAL_CALLME_BOT_URL}?phone={self.UUID}&apikey={self.api_key}&text={message}"
        response = requests.post(url)
        if f"Message sent to {self.UUID}!" not in response.text:
            raise Exception(f"Error during sending a message.\nServer response:\n{response.text}")
