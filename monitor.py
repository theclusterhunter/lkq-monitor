import json
import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hDPDOKcFOm"
SEEN_FILE = "seen_parts.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram missing token/chat id")
        print(message)
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=15
    )


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as file:
        return set(json.load(file))


def save_seen(seen):
    with open(SEEN_FILE, "w") as file:
        json.dump(sorted(list(seen)), file, indent=2)


def fetch_page():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=25)
    response.raise_for_status()
    return response.text


def extract_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    pattern = re.compile(
        r"Used Part\s+"
        r".*?~(?P<part>\d+).*?"
        r"Mileage:\s*(?P<mileage>[^\n]+).*?"
        r"Location:\s*(?P<location>[^\n]+).*?"
        r"Source:\s*(?P<source>[^\n]+).*?"
        r"Price:\s*(?P<price>\$[0-9,.]+)",
        re.DOTALL | re.IGNORECASE
    )

    listings = []

    for match in pattern.finditer(text):
        listings.append({
            "part": match.group("part").strip(),
            "source": match.group("source").strip(),
            "price": match.group("price").strip(),
            "mileage": match.group("mileage").strip(),
            "location": match.group("location").strip(),
        })

    return listings


def main():
    seen = load_seen()
    html = fetch_page()
    listings = extract_listings(html)

    if not listings:
        print("No listings found. LKQ page layout may have changed.")
        return

    updated_seen = set(seen)
    new_count = 0

    for item in listings:
        part_number = item["part"]

        if part_number not in seen:
            message = (
                "🚨 NEW LKQ CLUSTER\n\n"
                f"Source: {item['source']}\n"
                f"Price: {item['price']}\n"
                f"Part #: {item['part']}\n"
                f"Mileage: {item['mileage']}\n"
                f"Location: {item['location']}\n\n"
                f"{URL}"
            )

            send_alert(message)
            updated_seen.add(part_number)
            new_count += 1

    save_seen(updated_seen)

    print(f"Checked LKQ. Found {len(listings)} listings. New alerts sent: {new_count}")


if __name__ == "__main__":
    main()
