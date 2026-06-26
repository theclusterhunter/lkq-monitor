import requests
import os

URL = "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hDPDOKcFOm"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_alert(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message[:4000]},
        timeout=15
    )


headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

send_alert(
    "DEBUG LKQ RESPONSE\n\n"
    + response.text[:3000]
)
