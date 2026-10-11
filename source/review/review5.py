import json
from playwright.sync_api import sync_playwright

out = {}
URL = "http://127.0.0.1:8814/public/poker-hands.html"
with sync_playwright() as p:
    b = p.chromium.launch()

    # 1) JS disabled
    ctx = b.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
    pg = ctx.new_page(); pg.goto(URL, wait_until="load"); pg.wait_for_timeout(500)
    out["nojs_visible_text_len"] = len(pg.locator("body").inner_text())
    out["nojs_articles_visible"] = pg.locator("article").count()
    out["nojs_tab2_text"] = len(pg.locator('[role=tabpanel]').nth(1).inner_text())
    pg.screenshot(path="/tmp/poker-hands/review/16-nojs.png")
    ctx.close()

    # 2) a11y / focus / rapid switching
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(500)

    out["roles"] = pg.evaluate("""() => {
      const tl = document.querySelector('[role=tablist]');
      const tabs = [...document.querySelectorAll('[role=tab]')];
      const panels = [...document.querySelectorAll('[role=tabpanel]')];
      return {tablist: !!tl, tabs: tabs.map(t=>({id:t.id, controls:t.getAttribute('aria-controls'), tabindex:t.tabIndex})),
              panels: panels.map(p=>({id:p.id, labelledby:p.getAttribute('aria-labelledby'), hidden:p.hidden}))};
    }""")

    # focus ring check
    pg.keyboard.press("Tab")
    out["first_tab_focus_style"] = pg.evaluate("""() => { const e = document.activeElement;
      const cs = getComputedStyle(e); return {tag: e.tagName, outline: cs.outlineWidth + ' ' + cs.outlineStyle + ' ' + cs.outlineColor}; }""")

    # rapid double-click on second tab
    tab2 = pg.locator('[role=tab]').nth(1)
    tab2.click(); tab2.click(); pg.wait_for_timeout(300)
    out["rapid"] = pg.evaluate("""() => ({
        selected: document.querySelector('[role=tab][aria-selected=true]').textContent.trim(),
        visiblePanels: [...document.querySelectorAll('[role=tabpanel]')].filter(p=>!p.hidden).length,
        hiddenCount: [...document.querySelectorAll('[role=tabpanel]')].filter(p=>p.hidden).length})""")

    # click the same tab twice more + back
    pg.locator('[role=tab]').nth(0).click(); pg.wait_for_timeout(200)
    pg.locator('[role=tab]').nth(0).click(); pg.wait_for_timeout(200)
    out["click_same_tab_twice"] = pg.evaluate("""() => ({
        selected: document.querySelector('[role=tab][aria-selected=true]').textContent.trim(),
        visiblePanels: [...document.querySelectorAll('[role=tabpanel]')].filter(p=>!p.hidden).length})""")

    # aria-orientation / arrow keys on focused tab (already known broken) - test Tab key reachability
    pg.locator('[role=tab]').nth(0).focus()
    pg.keyboard.press("Tab")
    out["tab_from_tab1_lands_on"] = pg.evaluate("document.activeElement.textContent.trim().slice(0,40)")

    out["pageerrors"] = errs

    # 3) deep link / hash behavior (does #tab2 exist?)
    out["hash_links"] = pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))")

    # 4) contrast check on faint text
    out["contrast"] = pg.evaluate("""() => {
      const el = [...document.querySelectorAll('*')].find(e => e.children.length===0 && /possible combinations/.test(e.textContent));
      const cs = getComputedStyle(el); return {color: cs.color, fontSize: cs.fontSize, bg: getComputedStyle(document.body).backgroundColor};
    }""")
    b.close()

print(json.dumps(out, indent=1))
