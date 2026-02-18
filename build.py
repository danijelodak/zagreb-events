import json
from jinja2 import Template

events = json.load(open("events.json", encoding="utf-8"))
template = open("template.html", encoding="utf-8").read()

cards = ""

for e in events:
    date = e.get("date") or ""

    cards += f"""
    <div class="card"
         data-cat="{e.get('category','ostalo')}"
         data-date="{date}">
        <b>{e['title']}</b><br>
        {e['venue']}<br>
        {date}<br>
        <a href="{e['url']}" target="_blank">detalji</a>
    </div>
    """

html = Template(template).render(events=cards)

open("index.html", "w", encoding="utf-8").write(html)

print("index.html built — cards:", len(events))

