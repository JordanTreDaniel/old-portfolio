import json
from playwright.sync_api import sync_playwright

out = {}
URL = "http://127.0.0.1:8814/public/poker-hands.html"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1280, "height": 900}).new_page()
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(700)

    out["masthead"] = pg.evaluate("""() => {
      const m = document.querySelector('.masthead') || document.querySelector('header');
      const cs = getComputedStyle(m);
      return {h: Math.round(m.getBoundingClientRect().height), pos: cs.position, top: cs.top, z: cs.zIndex, bg: cs.backgroundColor};
    }""")

    # scroll so a hand is mid-view; check whether sticky rail gets covered by masthead
    pg.evaluate("window.scrollTo(0, 2500)"); pg.wait_for_timeout(500)
    out["rail_midscroll"] = pg.evaluate("""() => {
      const mast = (document.querySelector('.masthead')||document.querySelector('header')).getBoundingClientRect();
      const rails = [...document.querySelectorAll('.hand-rank')].map(r => {
        const b = r.getBoundingClientRect();
        return {text: r.innerText.replace('\\n','/'), top: Math.round(b.top), bottom: Math.round(b.bottom)};
      }).filter(r => r.bottom > 0 && r.top < innerHeight);
      return {mastBottom: Math.round(mast.bottom), rails};
    }""")
    pg.screenshot(path="/tmp/poker-hands/review/17-midscroll-sticky-rail.png")

    # deeper scroll to be sure a rail is stuck
    pg.evaluate("window.scrollTo(0, 4000)"); pg.wait_for_timeout(500)
    out["rail_midscroll2"] = pg.evaluate("""() => {
      const mast = (document.querySelector('.masthead')||document.querySelector('header')).getBoundingClientRect();
      const rails = [...document.querySelectorAll('.hand-rank')].map(r => {
        const b = r.getBoundingClientRect();
        return {text: r.innerText.replace('\\n','/'), top: Math.round(b.top), bottom: Math.round(b.bottom)};
      }).filter(r => r.bottom > 0 && r.top < innerHeight);
      return {mastBottom: Math.round(mast.bottom), rails, scrollY: scrollY};
    }""")
    pg.screenshot(path="/tmp/poker-hands/review/17b-midscroll-sticky-rail.png")

    # masthead height at mobile
    pg.set_viewport_size({"width": 380, "height": 800}); pg.wait_for_timeout(400)
    out["masthead_mobile"] = pg.evaluate("""() => {
      const m = document.querySelector('.masthead') || document.querySelector('header');
      return {h: Math.round(m.getBoundingClientRect().height)};
    }""")
    out["rail_css"] = pg.evaluate("""() => { const r = document.querySelector('.hand-rank'); const cs = getComputedStyle(r);
      return {pos: cs.position, top: cs.top}; }""")
    b.close()

print(json.dumps(out, indent=1))
