import json, os
from playwright.sync_api import sync_playwright

OUT = "/tmp/poker-hands/review"
URL = "http://127.0.0.1:8814/public/poker-hands.html"
rep = {}

def art(pg, name):
    return pg.locator(f'article:has(h3:text-is("{name}"))')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1280, "height": 950}).new_page()
    pg.goto(URL, wait_until="load")
    pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
    pg.wait_for_timeout(1200)

    # precise region screenshots (tab 1)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/01-desktop-top-royal-flush.png")
    for name, fn in [("Full house","02-desktop-full-house"), ("Flush","02b-desktop-flush"),
                     ("Two pair","03-desktop-two-pair"), ("High card","05-desktop-high-card-article")]:
        el = art(pg, name)
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(350)
        el.screenshot(path=f"{OUT}/{fn}.png")
    # bottom of page
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(400)
    pg.screenshot(path=f"{OUT}/04-desktop-page-bottom.png")

    # rank order + structural completeness check (exact heading-based)
    rep["hands"] = pg.evaluate("""() => [...document.querySelectorAll('article')].map(a => ({
        name: a.querySelector('h3').textContent.trim(),
        num: (a.innerText.match(/#\\d+/)||[])[0],
        imgs: [...a.querySelectorAll('img')].map(i=>i.getAttribute('src').split('/').pop()),
        hasBeats: /WHAT IT BEATS/i.test(a.innerText),
        hasWhy: /\\bWHY\\b/.test(a.innerText),
        hasTip: /BEGINNER TIP/.test(a.innerText),
        hasHow: /HOW IT HAPPENED/.test(a.innerText),
        odds: (a.innerText.match(/ODDS\\n([^\\n]+)/)||[])[1],
        combos: (a.innerText.match(/([\\d,]+) possible combinations/)||[])[1]
    }))""")

    # tab 2: per-example ring/dim audit vs JSON best5
    pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click(); pg.wait_for_timeout(1200)
    rep["examples_audit"] = pg.evaluate("""() => {
      const panel = [...document.querySelectorAll('[role=tabpanel]')].find(p => getComputedStyle(p).display !== 'none');
      return [...panel.querySelectorAll('section.example')].map(s => ({
        title: s.querySelector('.example-title')?.innerText.replace(/\\d+$/,'').trim(),
        hole: [...s.querySelectorAll('.zone-hole img')].map(i=>({f:i.src.split('/').pop(), cls:i.className})),
        board: [...s.querySelectorAll('.zone-board img')].map(i=>({f:i.src.split('/').pop(), cls:i.className})),
        ringed: [...s.querySelectorAll('img.ring, img[class*=ring]')].map(i=>i.src.split('/').pop()),
        dimmed: [...s.querySelectorAll('img.dimmed')].map(i=>i.src.split('/').pop()),
        zones: [...s.querySelectorAll('.zone-label')].map(e=>e.innerText.trim()),
        hasLegend: !!s.querySelector('[class*=legend]')
      }));
    }""")

    # zone bg colors both examples
    rep["zone_style"] = pg.evaluate("""() => {
      const z = document.querySelector('.zone-hole'), b = document.querySelector('.zone-board');
      const g = n => {const c=getComputedStyle(n); return {bg:c.backgroundColor, border:c.border, padding:c.padding};};
      return {hole:g(z), board:g(b)};
    }""")

    # precise tab2 screenshots
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(250)
    pg.screenshot(path=f"{OUT}/06-desktop-tab2-top.png")
    for i in range(5):
        el = pg.locator('section.example').nth(i)
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        el.screenshot(path=f"{OUT}/07-tab2-example-{i+1}.png")
    for name in ["primer","mistakes","glossary"]:
        el = pg.locator(f'.{name}').first
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        el.screenshot(path=f"{OUT}/08-tab2-{name}.png")

    # mobile re-check with precise shots
    pg.set_viewport_size({"width": 380, "height": 820}); pg.wait_for_timeout(400)
    pg.locator('[role="tab"]:has-text("HAND RANKINGS")').click(); pg.wait_for_timeout(300)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(250)
    pg.screenshot(path=f"{OUT}/09-mobile-380-top.png")
    art(pg, "Full house").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/10b-mobile-380-fullhouse.png")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(350)
    pg.screenshot(path=f"{OUT}/10c-mobile-380-bottom.png")
    pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click(); pg.wait_for_timeout(600)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(250)
    pg.screenshot(path=f"{OUT}/11-mobile-380-tab2.png")
    pg.locator('section.example').first.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/11b-mobile-380-tab2-example.png")
    rep["mobile_overflow"] = pg.evaluate("({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth})")
    rep["mobile_zone_widths"] = pg.evaluate("""() => [...document.querySelectorAll('.zone')].slice(0,4).map(z=>({cls:z.className, w:Math.round(z.getBoundingClientRect().width), right:Math.round(z.getBoundingClientRect().right)}))""")
    b.close()

json.dump(rep, open(f"{OUT}/report3.json","w"), indent=1, default=str)
print(json.dumps(rep, indent=1, default=str))
