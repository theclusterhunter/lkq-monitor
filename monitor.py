import json
import os
import re
import requests
from bs4 import BeautifulSoup

TRACKED_PAGES = {
    "CLUSTER": [
        "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hDPDOKcFOm",
        "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hKPDOKcFOm",
        "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hK4FOKcFOm",
        "https://www.lkqonline.com/2015-bmw-760-series-speedometer-head-cluster/-hPD3OKcFOm",
    ],
    "DME": [
        "https://www.lkqonline.com/2010-bmw-335i-engine-motor-control-module/-hKjFjOcn4O",
        "https://www.lkqonline.com/2010-bmw-335i-engine-motor-control-module/-hn4DmOcn4O",
    ],
}

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
        timeout=15,
    )


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    with open(SEEN_FILE, "r") as file:
        return set(json.load(file))


def save_seen(seen):
    with open(SEEN_FILE, "w") as file:
        json.dump(sorted(list(seen)), file, indent=2)


def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=25)
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
        re.DOTALL | re.IGNORECASE,
    )

    listings = []

    for match in pattern.finditer(text):
        listings.append(
            {
                "part": match.group("part").strip(),
                "source": match.group("source").strip(),
                "price": match.group("price").strip(),
                "mileage": match.group("mileage").strip(),
                "location": match.group("location").strip(),
            }
        )

    return listings


def make_message(category, item, url):
    if category == "CLUSTER":
        title = "📟 NEW CLUSTER FOUND"
    elif category == "DME":
        title = "🧠 NEW DME FOUND"
    else:
        title = "🚨 NEW LKQ PART FOUND"

    return (
        f"{title}\n\n"
        f"Source: {item['source']}\n"
        f"Price: {item['price']}\n"
        f"Part #: {item['part']}\n"
        f"Mileage: {item['mileage']}\n"
        f"Location: {item['location']}\n\n"
        f"Open LKQ:\n{url}"
    )


def main():
    seen = load_seen()
    updated_seen = set(seen)

    total_found = 0
    total_new = 0

    for category, urls in TRACKED_PAGES.items():
        for url in urls:
            try:
                html = fetch_page(url)
                listings = extract_listings(html)
                total_found += len(listings)

                if not listings:
                    print(f"No listings found for {category}: {url}")
                    continue

                for item in listings:
                    unique_key = f"{category}|{url}|{item['part']}"

                    if unique_key not in seen:
                        send_alert(make_message(category, item, url))
                        updated_seen.add(unique_key)
                        total_new += 1

            except Exception as e:
                print(f"Error checking {category} page {url}: {e}")

    save_seen(updated_seen)

    print(f"Finished. Total listings found: {total_found}. New alerts sent: {total_new}")


if __name__ == "__main__":
    main()
