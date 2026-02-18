import json

print("NEW SCRAPER FILE RUNNING")

events = [
    {
        "title": "NOVI SCRAPER RADI",
        "venue": "debug",
        "url": "https://example.com",
        "source": "debug"
    }
]

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

print("WROTE NEW EVENTS")