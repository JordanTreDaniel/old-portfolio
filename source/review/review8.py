import json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8814/public/poker-hands.html"
found = None
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1280, "height": 900}).new_page()
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(700)
    for y in range(1200, 6500, 60):
        pg.evaluate(f"window.scrollTo(0,{y})")
        pg.wait_for_timeout(60)
        r = pg.evaluate("""() => {
          const mast = document.querySelector('.masthead').getBoundingClientRect().bottom;
          const rails = [...document.querySelectorAll('.hand-rail')].map(x => {
            const b = x.getBoundingClientRect();
            return {txt: x.innerText.replace('\\n','/'), top: Math.round(b.top), bottom: Math.round(b.bottom)};
          }).filter(r => r.bottom > 0 && r.top < innerHeight);
          return {mast: Math.round(mast), rails, y: scrollY};
        }""")
        stuck = [x for x in r["rails"] if 100 <= x["top"] <= 170]
        if stuck:
            found = {"scroll": y, "mastBottom": r["mast"], "rails": r["rails"]}
            pg.screenshot(path="/tmp/poker-hands/review/18-stuck-rail.png")
            break
    print(json.dumps(found, indent=1))
    b.close()
