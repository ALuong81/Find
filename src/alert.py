import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def send(msg):

    if not TELEGRAM_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass


def send_image(path):

    if not TELEGRAM_TOKEN or path is None:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    try:
        with open(path, "rb") as f:
            requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": f})
    except:
        pass
