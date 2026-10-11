import json
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1280, "height": 950}).new_page()
    pg.goto("http://127.0.0.1:8814/public/poker-hands.html", wait_until="load")
    pg.wait_for_timeout(800)
    out["metrics"] = pg.evaluate("""() => {
      const a = [...document.querySelectorAll('article')].find(x => x.querySelector('h3').textContent.trim() === 'High card');
      const ar = a.getBoundingClientRect();
      const odds = a.querySelector('.odds');
      const orr = odds.getBoundingClientRect();
      const cs = getComputedStyle(a);
      return {articleL: ar.left, articleR: ar.right, padL: cs.paddingLeft, padR: cs.paddingRight,
              oddsR: orr.right, gapToArticleEdge: ar.right - orr.right,
              vw: innerWidth,
              docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
              footer: (document.querySelector('footer')||{}).innerText,
              tabs: [...document.querySelectorAll('[role=tab]')].map(t=>({txt:t.innerText.trim(), sel:t.getAttribute('aria-selected'), tag:t.tagName}))};
    }""")
    el = pg.locator('article:has(h3:text-is("High card"))')
    el.scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    pg.screenshot(path="/tmp/poker-hands/review/13-desktop-highcard-viewport.png")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(500)
    pg.screenshot(path="/tmp/poker-hands/review/04-desktop-page-bottom.png")
    # zoom test 150% at desktop width (simulates browser zoom): shrink viewport to 1280/1.5
    pg.set_viewport_size({"width": 853, "height": 633}); pg.wait_for_timeout(400)
    out["zoom150"] = pg.evaluate("({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth})")
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
    pg.screenshot(path="/tmp/poker-hands/review/14-zoom150-853w.png")
    # keyboard: tab to tabs and press Enter (a11y)
    pg.set_viewport_size({"width": 1280, "height": 950}); pg.wait_for_timeout(300)
    pg.locator('[role=tab]').first.focus()
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(400)
    out["kbd"] = pg.evaluate("""() => ({focus: document.activeElement.textContent.trim(),
        selected: document.querySelector('[role=tab][aria-selected=true]').textContent.trim()})""")
    b.close()

print(json.dumps(out, indent=1))
