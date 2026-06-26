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

    parts = re.findall(r"~(\d+)", text)
    prices = re.findall(r"\$[0-9,.]+", text)
    sources = re.findall(r"Source:\s*([^\n]+)", text, re.IGNORECASE)
    mileages = re.findall(r"Mileage:\s*([^\n]+)", text, re.IGNORECASE)
    locations = re.findall(r"Location:\s*([^\n]+)", text, re.IGNORECASE)

    listings = []
    count = min(len(parts), len(prices), len(sources))

    for i in range(count):
        listings.append({
            "part": parts[i],
            "source": sources[i],
            "price": prices[i],
            "mileage": mileages[i] if i < len(mileages) else "N/A",
            "location": locations[i] if i < len(locations) else "N/A",
        })

    return listings


def main():
    seen = load_seen()
    updated_seen = set(seen)

    total_found = 0
    total_new = 0
    debug_lines = []

    for category, urls in TRACKED_PAGES.items():
        for url in urls:
            try:
                html = fetch_page(url)
                listings = extract_listings(html)
                total_found += len(listings)

                debug_lines.append(f"{category}: found {len(listings)} listings")

                for item in listings:
                    unique_key = f"{category}|{url}|{item['part']}"

                    if unique_key not in seen:
                        send_alert(
                            f"{'📟 NEW CLUSTER FOUND' if category == 'CLUSTER' else '🧠 NEW DME FOUND'}\n\n"
                            f"Source: {item['source']}\n"
                            f"Price: {item['price']}\n"
                            f"Part #: {item['part']}\n"
                            f"Mileage: {item['mileage']}\n"
                            f"Location: {item['location']}\n\n"
                            f"Open LKQ:\n{url}"
                        )
                        updated_seen.add(unique_key)
                        total_new += 1

            except Exception as e:
                debug_lines.append(f"{category}: ERROR {e}")

    save_seen(updated_seen)

    send_alert(
        "✅ LKQ BOT CHECK COMPLETE\n\n"
        f"Total listings found: {total_found}\n"
        f"New alerts sent: {total_new}\n\n"
        + "\n".join(debug_lines)
    )


if __name__ == "__main__":
    main()
