import json, os, re
from playwright.sync_api import sync_playwright

OUT = "/tmp/poker-hands/review"
os.makedirs(OUT, exist_ok=True)
URL = "http://127.0.0.1:8814/public/poker-hands.html"

report = {"console": [], "pageerrors": [], "requests_failed": []}

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.on("console", lambda m: report["console"].append(f"{m.type}: {m.text}"))
    pg.on("pageerror", lambda e: report["pageerrors"].append(str(e)))
    pg.on("requestfailed", lambda r: report["requests_failed"].append(f"{r.url} :: {r.failure}"))

    pg.goto(URL, wait_until="load")
    pg.evaluate("window.__noReloadMarker = 'alive'")

    # force-load lazy images by scrolling through the page
    h = pg.evaluate("document.body.scrollHeight")
    y = 0
    while y < h:
        pg.evaluate(f"window.scrollTo(0,{y})")
        pg.wait_for_timeout(150)
        y += 700
        h = pg.evaluate("document.body.scrollHeight")
    pg.wait_for_timeout(800)

    imgs = pg.evaluate("""() => [...document.images].map(i => ({
        src: i.getAttribute('src').split('/').pop(),
        nw: i.naturalWidth, nh: i.naturalHeight,
        w: Math.round(i.getBoundingClientRect().width),
        h: Math.round(i.getBoundingClientRect().height),
        loaded: i.complete
    }))""")
    report["images"] = {
        "total": len(imgs),
        "broken": [i for i in imgs if i["nw"] == 0],
        "zero_display_size": [i for i in imgs if i["w"] == 0 or i["h"] == 0],
        "sample_sizes": imgs[:3],
    }

    # desktop overflow
    report["desktop_overflow"] = pg.evaluate(
        "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")

    # --- Tab 1 screenshots ---
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/01-desktop-top-royal-flush.png")

    # full house region
    fh = pg.locator("article", has_text="Full house").first
    fh.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    fh.screenshot(path=f"{OUT}/02-desktop-full-house.png")

    # two pair region
    tp = pg.locator("article", has_text="Two pair").first
    tp.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    tp.screenshot(path=f"{OUT}/03-desktop-two-pair.png")

    # bottom: high card
    hc = pg.locator("article", has_text="High card").first
    hc.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/04-desktop-bottom-high-card-viewport.png")
    hc.screenshot(path=f"{OUT}/05-desktop-high-card-article.png")

    # --- tab switch test (no reload) ---
    pg.evaluate("window.scrollTo(0,0)")
    pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click()
    pg.wait_for_timeout(500)
    report["tab_switch_marker"] = pg.evaluate("window.__noReloadMarker || null")
    report["tab2_selected"] = pg.evaluate(
        "document.querySelector('[role=tab][aria-selected=true]')?.textContent.trim()")
    report["tab1_hidden"] = pg.evaluate(
        """() => {
            const t1 = document.querySelectorAll('[role=tabpanel]')[0];
            return {hidden: t1.hidden || getComputedStyle(t1).display === 'none',
                    rect: t1.getBoundingClientRect().height};
        }""")
    pg.screenshot(path=f"{OUT}/06-desktop-tab2-top.png")

    # tab2 content audit
    report["tab2"] = pg.evaluate("""() => {
        const panel = [...document.querySelectorAll('[role=tabpanel]')].find(p => getComputedStyle(p).display !== 'none');
        const txt = panel.innerText;
        const imgs = [...panel.querySelectorAll('img')].map(i => i.getAttribute('src').split('/').pop());
        const h = [...panel.querySelectorAll('h2,h3,h4')].map(e => e.textContent.trim());
        return {
          headings: h,
          imgCount: imgs.length,
          imgs: imgs,
          hasPrimer: txt.includes('What is a') || txt.includes('hole card'),
          hasMistakes: /mistake/i.test(txt),
          hasGlossary: /glossary/i.test(txt),
          best5Count: (txt.match(/best 5|BEST 5/gi)||[]).length,
          textLen: txt.length,
          excerpt: txt.slice(0, 700)
        };
    }""")

    # scroll through tab2 capturing regions
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(200)
    # first interaction example
    for i in range(3):
        try:
            el = pg.locator("[class*=example], [class*=interaction]").nth(i)
            el.scroll_into_view_if_needed()
            pg.wait_for_timeout(250)
            el.screenshot(path=f"{OUT}/07-tab2-example-{i+1}.png")
        except Exception as e:
            report.setdefault("shot_errors", []).append(str(e))
    # glossary / mistakes sections
    for name, pat in [("mistakes", "text=Mistakes"), ("glossary", "text=Glossary")]:
        try:
            el = pg.locator(pat).first
            el.scroll_into_view_if_needed()
            pg.wait_for_timeout(250)
            sec = el.evaluate_handle("e => e.closest('section') || e.parentElement")
            sec.as_element().screenshot(path=f"{OUT}/08-tab2-{name}.png")
        except Exception as e:
            report.setdefault("shot_errors", []).append(f"{name}: {e}")

    # tab switch back and forth x3, check layout integrity
    for i in range(3):
        pg.locator('[role="tab"]:has-text("HAND RANKINGS")').click()
        pg.wait_for_timeout(150)
        pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click()
        pg.wait_for_timeout(150)
    report["after_3_switches_marker"] = pg.evaluate("window.__noReloadMarker || null")
    report["after_switches_overflow"] = pg.evaluate(
        "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")

    # --- mobile 380px ---
    pg.set_viewport_size({"width": 380, "height": 800})
    pg.wait_for_timeout(400)
    # back to tab 1 for rankings check
    pg.locator('[role="tab"]:has-text("HAND RANKINGS")').click()
    pg.wait_for_timeout(300)
    report["mobile_overflow"] = pg.evaluate(
        "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
    # find any element wider than viewport
    report["mobile_wide_elements"] = pg.evaluate("""() => {
        const vw = document.documentElement.clientWidth;
        return [...document.querySelectorAll('body *')]
          .filter(e => e.getBoundingClientRect().right > vw + 1 || e.getBoundingClientRect().width > vw + 1)
          .slice(0, 15)
          .map(e => ({tag: e.tagName, cls: (e.className||'').toString().slice(0,60),
                      w: Math.round(e.getBoundingClientRect().width),
                      right: Math.round(e.getBoundingClientRect().right)}));
    }""")
    # small text check
    report["mobile_small_text"] = pg.evaluate("""() => {
        const bad = [];
        for (const e of document.querySelectorAll('p, span, li, dd, dt, h1,h2,h3,h4, div')) {
            if (!e.children.length && e.textContent.trim()) {
                const fs = parseFloat(getComputedStyle(e).fontSize);
                if (fs < 11) bad.push({t: e.textContent.trim().slice(0,40), fs});
            }
        }
        return bad.slice(0, 10);
    }""")
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/09-mobile-380-top.png")
    hcm = pg.locator("article", has_text="High card").first
    hcm.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/10-mobile-380-highcard.png")
    # tab2 on mobile
    pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click()
    pg.wait_for_timeout(300)
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(200)
    pg.screenshot(path=f"{OUT}/11-mobile-380-tab2.png")
    report["mobile_overflow_tab2"] = pg.evaluate(
        "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")

    # tiny widths stress: 320
    pg.set_viewport_size({"width": 320, "height": 700})
    pg.wait_for_timeout(300)
    report["w320_overflow"] = pg.evaluate(
        "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
    pg.screenshot(path=f"{OUT}/12-mobile-320-tab2.png")

    b.close()

with open(f"{OUT}/report.json", "w") as f:
    json.dump(report, f, indent=1, default=str)
print(json.dumps(report, indent=1, default=str)[:6000])
