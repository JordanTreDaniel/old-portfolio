import json, os
from playwright.sync_api import sync_playwright

OUT = "/tmp/poker-hands/review"
URL = "http://127.0.0.1:8814/public/poker-hands.html"
rep = {}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.locator('[role="tab"]:has-text("HOW CARDS COMBINE")').click()
    pg.wait_for_timeout(1500)

    # all tab2 images loaded now?
    rep["tab2_imgs"] = pg.evaluate("""() => {
      const panel = [...document.querySelectorAll('[role=tabpanel]')].find(p => getComputedStyle(p).display !== 'none');
      const imgs = [...panel.querySelectorAll('img')];
      return {total: imgs.length, broken: imgs.filter(i => i.naturalWidth === 0).map(i=>i.src.split('/').pop()),
              zeroSize: imgs.filter(i => i.getBoundingClientRect().width === 0).length};
    }""")

    # structure of each example: hole / board / best5 groups + highlight classes + computed styles
    rep["examples"] = pg.evaluate("""() => {
      const panel = [...document.querySelectorAll('[role=tabpanel]')].find(p => getComputedStyle(p).display !== 'none');
      return [...panel.querySelectorAll('[class*=example]')].map(el => {
        const groups = {};
        for (const sel of ['[class*=hole]','[class*=board]','[class*=best]','[class*=dim]','[class*=ring]']) {
          groups[sel] = [...el.querySelectorAll(sel)].map(n => ({cls: n.className, imgs: [...n.querySelectorAll('img')].map(i=>i.src.split('/').pop())}));
        }
        return {title: el.innerText.split('\\n')[0].slice(0,70), groups, html: el.outerHTML.slice(0, 400)};
      });
    }""")

    # glossary terms rendered
    rep["glossary"] = pg.evaluate("""() => [...document.querySelectorAll('.glossary dt, .glossary [class*=term]')].map(e=>e.textContent.trim())""")
    rep["traps"] = pg.evaluate("""() => [...document.querySelectorAll('.mistakes li')].map(e=>e.textContent.trim().slice(0,70))""")
    rep["trapsCount"] = pg.evaluate("document.querySelectorAll('.mistakes li').length")

    # take clean screenshots of tab2 sections
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
    pg.screenshot(path=f"{OUT}/06-desktop-tab2-top.png")
    for i in range(5):
        try:
            el = pg.locator('[class*=example]').nth(i)
            el.scroll_into_view_if_needed(); pg.wait_for_timeout(250)
            el.screenshot(path=f"{OUT}/07-tab2-example-{i+1}.png")
        except Exception as e:
            rep.setdefault("errs", []).append(f"ex{i}: {e}")
    for name in ["primer", "mistakes", "glossary"]:
        try:
            el = pg.locator(f"section.{name}, aside.{name}, [class*={name}]").first
            el.scroll_into_view_if_needed(); pg.wait_for_timeout(250)
            el.screenshot(path=f"{OUT}/08-tab2-{name}.png")
        except Exception as e:
            rep.setdefault("errs", []).append(f"{name}: {e}")

    # visual distinctness: computed background/border of hole vs board vs best5 containers
    rep["styling"] = pg.evaluate("""() => {
      const panel = [...document.querySelectorAll('[role=tabpanel]')].find(p => getComputedStyle(p).display !== 'none');
      const pick = sel => { const n = panel.querySelector(sel); if(!n) return null;
        const cs = getComputedStyle(n);
        return {sel, cls: n.className, bg: cs.backgroundColor, border: cs.borderColor, opacity: cs.opacity, outline: cs.outline}; };
      return ['[class*=hole]','[class*=board]','[class*=best]','[class*=dim]'].map(pick);
    }""")

    # hand-rankings visual weight: number font sizes top vs bottom
    pg.locator('[role="tab"]:has-text("HAND RANKINGS")').click(); pg.wait_for_timeout(400)
    rep["type_scale"] = pg.evaluate("""() => {
      const arts = [...document.querySelectorAll('article')];
      const f = a => { const h = a.querySelector('h3'); const num = a.querySelector('[class*=num], [class*=index], [class*=rank]');
        return {name: h.textContent.trim(), h3: getComputedStyle(h).fontSize,
                num: num ? getComputedStyle(num).fontSize : null}; };
      return {first: f(arts[0]), last: f(arts[arts.length-1]),
              accent: getComputedStyle(arts[0]).borderLeftColor,
              allSame: new Set(arts.map(a=>getComputedStyle(a.querySelector('h3')).fontSize)).size === 1};
    }""")

    # font check: does mobile use rem scaling? sample computed font-size of body text at 380
    pg.set_viewport_size({"width": 380, "height": 800}); pg.wait_for_timeout(300)
    rep["mobile_body_font"] = pg.evaluate("""() => {
      const p = document.querySelector('article p');
      const h3 = document.querySelector('article h3');
      return {p: p ? getComputedStyle(p).fontSize : null, h3: h3 ? getComputedStyle(h3).fontSize : null,
              beats: (()=>{const b=[...document.querySelectorAll('*')].find(e=>e.textContent.trim()==='what it beats'); return b?getComputedStyle(b).fontSize:null})()};
    }""")
    rep["pageerrors"] = errs
    b.close()

json.dump(rep, open(f"{OUT}/report2.json","w"), indent=1, default=str)
print(json.dumps(rep, indent=1, default=str)[:7000])
