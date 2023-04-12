from pathlib import Path
import json
from datetime import datetime

from signal import SignalCallMeBot

SIGNAL_BOT_DIR_PATH = Path(__file__).parent.resolve()
CONFIGS_DIR_PATH = SIGNAL_BOT_DIR_PATH / "configs"

DEFAULT_CONFIG_PATH = CONFIGS_DIR_PATH / "sanity_check.json"


def get_config() -> dict:
    with open(DEFAULT_CONFIG_PATH, 'r') as config:
        return json.loads(config.read())


if __name__ == "__main__":
    config = get_config()
    signal_bot = SignalCallMeBot(uuid=config['uuid'], api_key=config['apikey'])
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    signal_bot.send_message(f"[TEST] Today is -> {date}")
