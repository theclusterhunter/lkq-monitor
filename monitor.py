import hashlib
import os
import requests

URL = "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hDPDOKcFOm"

HASH_FILE = "page_hash.txt"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        print(message)
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=15
    )


def get_page_hash():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=25)
    response.raise_for_status()

    page_text = response.text

    return hashlib.sha256(page_text.encode("utf-8")).hexdigest()


def load_old_hash():
    if not os.path.exists(HASH_FILE):
        return None

    with open(HASH_FILE, "r") as file:
        return file.read().strip()


def save_new_hash(new_hash):
    with open(HASH_FILE, "w") as file:
        file.write(new_hash)


def main():
    old_hash = load_old_hash()
    new_hash = get_page_hash()

    send_alert("✅ TEST SUCCESS — LKQ bot is connected to Telegram and running from GitHub.")

print("Telegram test sent.")

    save_new_hash(new_hash)


if __name__ == "__main__":
    main()
