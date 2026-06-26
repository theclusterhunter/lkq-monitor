import json
import os
import re
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hDPDOKcFOm"
]

SEEN_FILE = "seen.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    })


def check_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    title = soup.title.get_text(strip=True) if soup.title else "LKQ Listing"

    price_match = re.search(r"\$\s?[0-9,]+(?:\.\d{2})?", text)
    price = price_match.group(0) if price_match else "Price not found"

    unavailable_words = ["out of stock", "not available", "sold", "removed"]
    status = "Possibly available"

    if any(word in text.lower() for word in unavailable_words):
        status = "May be unavailable/sold"

    listing_key = f"{url}|{price}|{status}"

    return listing_key, title, price, status, url


def main():
    seen = load_seen()
    new_seen = set(seen)

    for url in URLS:
        try:
            listing_key, title, price, status, link = check_page(url)

            if listing_key not in seen:
                msg = f"LKQ update found:\n\n{title}\nPrice: {price}\nStatus: {status}\n\n{link}"
                print(msg)
                send_telegram(msg)
                new_seen.add(listing_key)
            else:
                print(f"No change: {url}")

        except Exception as e:
            print(f"Error checking {url}: {e}")

    save_seen(new_seen)


if __name__ == "__main__":
    main()
