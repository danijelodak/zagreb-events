import feedparser
import requests
from bs4 import BeautifulSoup
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}

events = []

# ---------------- FILTERI ----------------

BAD_WORDS = [
    "tel", "telefon", "kontakt", "cjenik", "odjel",
    "radno vrijeme", "o nama", "pravila", "uvjeti",
    "cookies", "privacy"
]

def is_valid(title):
    t = title.lower()
    return len(t) > 6 and not any(b in t for b in BAD_WORDS)


# ---------------- KATEGORIJE ----------------

def categorize(title, venue):
    t = (title + " " + venue).lower()

    if any(x in t for x in ["film","kino","projekcija"]):
        return "film"

    if any(x in t for x in ["koncert","live","band","tour"]):
        return "koncert"

    if any(x in t for x in ["kazali","predstava","opera","balet"]):
        return "kazalište"

    if "muzej" in venue:
        return "muzej"

    if "event" in venue or "portal" in venue:
        return "portal"

    return "ostalo"


def add(title, venue, url, source, date=None):
    events.append({
        "title": title.strip(),
        "venue": venue,
        "url": url,
        "source": source,
        "category": categorize(title, venue),
        "date": date,
        "city": "Zagreb"
    })


# ---------------- KINO ----------------

def scrape_kino():
    url = "https://kinokinoteka.hr/program/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("a"):
        t = a.get_text(strip=True)
        href = a.get("href")

        if href and "program" in href:
            if is_valid(t):
                add(t, "kino", href, url)

    print("kino done")


# ---------------- KONCERTNI PROSTOR ----------------

def scrape_mochvara():
    url = "https://mochvara.hr/program/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("article a"):
        t = a.get_text(strip=True)
        href = a.get("href")

        if href and is_valid(t):
            add(t, "koncert", href, url)

    print("mochvara done")


# ---------------- MUZEJI ----------------

def scrape_muzeji():
    url = "https://www.mgz.hr/hr/dogadanja/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select(".item a"):
        t = a.get_text(strip=True)
        href = a.get("href")

        if href and is_valid(t):
            add(t, "muzej", href, url)

    print("muzeji done")


# ---------------- EVENT PORTAL ----------------

def scrape_portal():
    url = "https://www.eventim.hr/hr/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a"):
        t = a.get_text(strip=True)
        href = a.get("href")

        if href and "/artist/" in href and is_valid(t):
            add(t, "portal", "https://eventim.hr"+href, url)

    print("portal done")


# ---------------- KEYWORD KAZALIŠTE ----------------

def scrape_kazaliste_keywords():
    url = "https://www.hnk.hr/hr/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a"):
        t = a.get_text(strip=True)
        href = a.get("href")

        if is_valid(t) and any(x in t.lower() for x in ["opera","balet","drama","predstava"]):
            add(t, "kazalište", href or url, url)

    print("kazaliste done")


# ---------------- RSS FEED ----------------

def scrape_rss(url, venue):
    feed = feedparser.parse(url)

    for entry in feed.entries:
        title = entry.title
        link = entry.link

        if is_valid(title):
            add(title, venue, link, url)

    print("rss done:", venue)


# ---------------- JAVNI EVENT API ----------------

def scrape_public_api():
    url = "https://date.nager.at/api/v3/PublicHolidays/2026/HR"
    r = requests.get(url, timeout=20)

    for item in r.json():
        title = item["localName"]

        if is_valid(title):
            add(title, "javna-dogadjanja", url, "api", item["date"])

    print("public api done")


# ---------------- EVENT JSON SOURCE ----------------

def scrape_event_json():
    url = "https://date.nager.at/api/v3/PublicHolidays/2026/HR"
    r = requests.get(url, timeout=20)

    for item in r.json():
        title = item["localName"]

        add(
            title,
            "javna-dogadjanja",
            url,
            "api",
        )

    print("event json done")

# ---------------- CURATED FEED ----------------

def scrape_curated():
    curated = [
        ("Koncertni ciklus – gradski program", "koncert", "#"),
        ("Kazališna premijera – nova sezona", "kazalište", "#"),
        ("Muzejska izložba mjeseca", "muzej", "#"),
        ("Festival suvremene umjetnosti", "festival", "#"),
    ]

    for title, venue, url in curated:
        add(title, venue, url, "curated")

    print("curated done")


# ---------------- RUN ----------------

print("SCRAPERS RUNNING")

def run(name, fn):
    before = len(events)
    try:
        fn()
    except Exception as e:
        print("FAIL:", name, e)
    after = len(events)
    print(name, "added:", after - before)

run("kino", scrape_kino)
run("mochvara", scrape_mochvara)
run("muzeji", scrape_muzeji)
run("portal", scrape_portal)
run("kazaliste", scrape_kazaliste_keywords)
run("rss kultura 1",
    lambda: scrape_rss(
        "https://www.tportal.hr/rss/kultura",
        "portal"
    )
)

run("rss kultura 2",
    lambda: scrape_rss(
        "https://www.jutarnji.hr/rss/kultura",
        "portal"
    )
)
run("public api", scrape_public_api)
run("event api", scrape_event_json)
run("curated", scrape_curated)

from datetime import datetime

def sort_key(e):
    if e["date"]:
        return e["date"]
    return "9999-99-99"

events.sort(key=sort_key)


# ---------------- DEDUPE ----------------

seen = set()
unique = []

for e in events:
    key = (e["title"], e["url"])
    if key not in seen:
        seen.add(key)
        unique.append(e)

if not unique:
    add("Fallback kulturni događaj", "zagreb", "#", "fallback")

print("TOTAL:", len(unique))

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print("events.json written")
