import json, os, re, requests
from bs4 import BeautifulSoup

SEARCH_URLS = [
    "https://www.lkqonline.com/search?keyword=bmw%20speedometer%20cluster",
    "https://www.lkqonline.com/search?keyword=bmw%206wb%20cluster",
    "https://www.lkqonline.com/search?keyword=bmw%20head%20cluster",
]

SEEN_FILE = "seen.json"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    return set(json.load(open(SEEN_FILE)))

def save_seen(seen):
    json.dump(sorted(seen), open(SEEN_FILE, "w"), indent=2)

def alert(msg):
    if BOT_TOKEN and CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
    print(msg)

def extract_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)

        if "speedometer" in text.lower() or "cluster" in text.lower():
            if href.startswith("/"):
                href = "https://www.lkqonline.com" + href

            listing_id_match = re.search(r"~(\d+)", href)
            listing_id = listing_id_match.group(1) if listing_id_match else href

            listings.append({
                "id": listing_id,
                "title": text[:120],
                "url": href
            })

    return listings

def main():
    seen = load_seen()
    updated_seen = set(seen)

    headers = {"User-Agent": "Mozilla/5.0"}

    for url in SEARCH_URLS:
        r = requests.get(url, headers=headers, timeout=25)
        r.raise_for_status()

        listings = extract_listings(r.text)

        for item in listings:
            if item["id"] not in seen:
                alert(
                    "NEW LKQ CLUSTER LISTING\n\n"
                    f"{item['title']}\n\n"
                    f"{item['url']}"
                )
                updated_seen.add(item["id"])

    save_seen(updated_seen)

if __name__ == "__main__":
    main()
