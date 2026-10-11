import json
from playwright.sync_api import sync_playwright

out = {}
URL = "http://127.0.0.1:8814/public/poker-hands.html"
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(600)
    out["scrollY"] = pg.evaluate("window.scrollY") if False else "n/a (js off)"
    names = ["Royal flush", "Straight flush", "Four of a kind", "Full house", "Flush",
             "Straight", "Three of a kind", "Two pair", "One pair", "High card"]
    out["visible_articles_nojs"] = [n for n in names if pg.locator(f'article:has(h3:text-is("{n}"))').first.is_visible()]
    out["intro_visible_nojs"] = pg.locator("text=All ten poker hands").first.is_visible()
    out["tab2_primer_visible_nojs"] = pg.locator("text=What is a").first.is_visible()
    out["tab2_combos_visible_nojs"] = pg.locator("text=Using BOTH hole cards").first.is_visible()
    out["glossary_visible_nojs"] = pg.locator(".glossary").first.is_visible()
    pg.screenshot(path="/tmp/poker-hands/review/16-nojs.png")
    ctx.close()

    # JS on: verify class-based visibility through rapid interactions
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(500)

    def state():
        return pg.evaluate("""() => ({
            sel: document.querySelector('[role=tab][aria-selected=true]').dataset.tab,
            visible: [...document.querySelectorAll('.tab-panel')].filter(p=>getComputedStyle(p).display!=='none').map(p=>p.dataset.panel),
            hash: location.hash
        })""")

    out["initial"] = state()
    pg.locator('[role=tab]').nth(1).click(); pg.wait_for_timeout(250); out["after_click_tab2"] = state()
    pg.locator('[role=tab]').nth(1).click(); pg.wait_for_timeout(250); out["after_click_tab2_again"] = state()
    pg.locator('[role=tab]').nth(0).click(); pg.wait_for_timeout(250); out["after_click_tab1"] = state()
    pg.locator('[role=tab]').nth(0).click(); pg.wait_for_timeout(250); out["after_click_tab1_again"] = state()
    # double click fast (dblclick)
    pg.locator('[role=tab]').nth(1).dblclick(); pg.wait_for_timeout(300); out["after_dblclick_tab2"] = state()
    # hash deep link works?
    pg.goto(URL + "#combine", wait_until="load"); pg.wait_for_timeout(500); out["deep_link_combine"] = state()
    pg.goto(URL + "#garbage", wait_until="load"); pg.wait_for_timeout(500); out["deep_link_garbage"] = state()
    out["pageerrors"] = errs
    b.close()

print(json.dumps(out, indent=1))
