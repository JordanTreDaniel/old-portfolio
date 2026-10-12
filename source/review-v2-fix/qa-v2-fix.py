#!/usr/bin/env python3
"""Post-fix QA for poker-hands-v2. Local server on :8734 (v2 dir)."""
import json, re, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8734/poker-hands-v2.html'
OUT = pathlib.Path('/tmp/poker-hands/review-v2-fix')
OUT.mkdir(parents=True, exist_ok=True)
fails = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ((' — ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def vis(page, sel):
    return page.evaluate("""(sel) => { const e = document.querySelector(sel); if(!e) return 'MISSING';
        const s = getComputedStyle(e); const r = e.getBoundingClientRect();
        return s.display + '|' + ((r.width>0 && r.height>0) ? 'rendered' : 'ZERO'); }""", sel)


console, errors = [], []
with sync_playwright() as p:
    br = p.chromium.launch(args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'[:200]))
    page.on('pageerror', lambda e: errors.append(str(e)[:200]))
    page.goto(BASE, wait_until='load')
    page.wait_for_timeout(500)

    # ---------- OG IMAGE (1200x630 hero capture) ----------
    og_ctx = br.new_context(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
    og_page = og_ctx.new_page()
    og_page.goto(BASE, wait_until='load')
    og_page.wait_for_timeout(1200)
    og_page.screenshot(path='/tmp/poker-hands/v2/og-image.png')
    og_ctx.close()

    # ---------- heading outline ----------
    heads = page.evaluate("""Array.from(document.querySelectorAll('h1,h2,h3,h4'))
        .map(h => h.tagName + ': ' + h.textContent.trim().slice(0,60))""")
    (OUT / 'headings.txt').write_text('\n'.join(heads))
    h1 = page.evaluate("document.querySelector('h1').textContent.trim()")
    check('h1 contains "Poker Hands for Beginners"', 'Poker Hands for Beginners' in h1, h1)
    quiz_h2 = page.evaluate("""Array.from(document.querySelectorAll('.quiz-zone h2')).map(h=>h.textContent.trim())""")
    check('quiz zone has its own <h2>', quiz_h2 == ['Test yourself'], quiz_h2)
    # quiz questions must nest under the quiz h2, not the glossary h2
    outline_ok = page.evaluate("""() => {
        const h2s = Array.from(document.querySelectorAll('h2'));
        const quizH2 = document.querySelector('.quiz-zone h2');
        const i = h2s.indexOf(quizH2);
        const prev = h2s[i-1], next = h2s[i+1];
        return {prev: prev && prev.textContent.trim(), next: next && next.textContent.trim(),
                q4_under_quiz: (() => { const h4 = document.querySelector('#q1 .q-title');
                    let n = h4, chain = [];
                    while (n && n.tagName !== 'BODY') { if (/^H[1-6]$/.test(n.tagName)) chain.push(n.tagName); n = n.parentElement; }
                    return chain.join('<'); })()};
    }""")
    check('glossary h2 comes BEFORE quiz h2', outline_ok['prev'] == 'Glossary', outline_ok)
    heads_seq = [int(h[1]) for h in heads if h[1].isdigit()]
    skips = [(heads[i - 1], heads[i]) for i in range(1, len(heads_seq))
             if heads_seq[i] - heads_seq[i - 1] > 1]
    check('heading document-order has no level skips (h2->h3->h4 ok)', not skips, skips)
    check('q1 title is h4 (h2/h3 precede it in document order)',
          outline_ok['q4_under_quiz'] in ('H4', 'H4<H2', 'H4<H3<H2'), outline_ok['q4_under_quiz'])

    # ---------- meta tags ----------
    og = page.evaluate("""() => ({
        ogimage: document.querySelector('meta[property="og:image"]')?.content,
        twimage: document.querySelector('meta[name="twitter:image"]')?.content,
        twcard: document.querySelector('meta[name="twitter:card"]')?.content})""")
    check('og:image absolute URL', og['ogimage'] == 'https://portfolio.jordanchristley.com/public/poker-hands-v2/og-image.png', og)
    check('twitter:image present + large card', og['twimage'] == og['ogimage'] and og['twcard'] == 'summary_large_image', og)

    # ---------- FAQ JSON-LD ----------
    ld = page.evaluate("""() => { const s = JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent);
        return {n: s.mainEntity.length, names: s.mainEntity.map(q=>q.name)}; }""")
    check('FAQ has 9 Q&As incl. teaching question', ld['n'] == 9 and any('teach' in n.lower() for n in ld['names']), ld['names'][-1])

    # ---------- teacher note ----------
    tn = page.evaluate("document.querySelector('.teacher-note')?.textContent.trim()")
    check('teacher note present', bool(tn) and 'Coaching tip' in tn, tn)

    # ---------- @supports fallback ----------
    sup = page.evaluate("""() => {
        const supportsRules = [];
        for (const sheet of document.styleSheets) {
          let rules; try { rules = sheet.cssRules; } catch(e) { continue; }
          for (const r of rules) if (r.conditionText) supportsRules.push({cond: r.conditionText, n: r.cssRules.length});
        }
        return {parsed: CSS.supports('selector(:has(*))'), rules: supportsRules,
                revealDefault: getComputedStyle(document.querySelector('#q1 .reveal-wrong')).display,
                noHasNote: getComputedStyle(document.querySelector('.no-has-note')).display}; }""")
    has_sup = any(r['cond'].replace(' ', '') == 'not(selector(:has(*)))' for r in sup['rules'])
    check('@supports block PARSES (CSSSupportsRule in CSSOM)', has_sup, sup['rules'])
    check('modern Chrome: :has() supported, so block inert', sup['parsed'] is True)
    check('modern Chrome: reveals still hidden by default', sup['revealDefault'] == 'none', sup['revealDefault'])
    check('modern Chrome: no-has note still hidden', sup['noHasNote'] == 'none', sup['noHasNote'])

    # ---------- prove the fallback branch's declarations actually work ----------
    fb = page.evaluate("""() => {
        let decls = [];
        for (const sheet of document.styleSheets) {
          let rules; try { rules = sheet.cssRules; } catch(e) { continue; }
          for (const r of rules) {
            if (r.conditionText && r.conditionText.replace(/ /g,'') === 'not(selector(:has(*)))') {
              for (const inner of r.cssRules) decls.push(inner.cssText);
            }
          }
        }
        const st = document.createElement('style');
        st.textContent = decls.join('\\n');
        document.head.appendChild(st);
        const out = {
          decls,
          wrongReveal: getComputedStyle(document.querySelector('#q1 .reveal-wrong')).display,
          winReveal: getComputedStyle(document.querySelector('#q1 .reveal-win')).display,
          tag: getComputedStyle(document.querySelector('#q1 .reveal-wrong .reveal-tag')).display,
          best: getComputedStyle(document.querySelector('#q1 .reveal-best')).display,
          note: getComputedStyle(document.querySelector('.no-has-note')).display,
          selected: null};
        // selected-state feedback without :has() (sibling rule, shipped outside @supports)
        const cb = document.querySelector('#q1-qcheck-best, #q1-b1');
        cb.checked = true;
        out.selected = getComputedStyle(document.querySelector('label[for="q1-b1"]')).outlineColor;
        cb.checked = false;
        document.head.removeChild(st);
        out.after = getComputedStyle(document.querySelector('#q1 .reveal-wrong')).display;
        return out; }""")
    check('fallback: reveals forced visible', fb['wrongReveal'] == 'block' and fb['winReveal'] == 'block', fb['decls'])
    check('fallback: conditional tags/deselect lines hidden', fb['tag'] == 'none' and fb['best'] == 'none', (fb['tag'], fb['best']))
    check('fallback: update-browser note shown', fb['note'] == 'block', fb['note'])
    check('fallback: selected-card outline works without :has()', '255, 215, 0' in fb['selected'], fb['selected'])
    check('fallback: rules removed -> modern behavior restored', fb['after'] == 'none', fb['after'])

    # ---------- switch to quiz mode ----------
    page.click('label[for="tab-input-combine"]')
    page.wait_for_timeout(200)
    page.click('label[for="mode-input-quiz"]')
    page.wait_for_timeout(200)

    # ---------- qk kicker duel: single coherent wrong note ----------
    page.click('#qk label[for="qk-w1"]')  # a wrong card in the duel
    page.wait_for_timeout(150)
    qk_text = page.evaluate("document.querySelector('#qk .reveal-wrong').innerText")
    print('--- qk wrong reveal ---\n' + qk_text + '\n---')
    check('qk wrong reveal renders', vis(page, '#qk .reveal-wrong').startswith('block'))
    check('qk note is ONE paragraph (single <p>)',
          page.evaluate("document.querySelectorAll('#qk .reveal-wrong p').length") == 2)  # note + reveal-best
    check('qk note no longer stitched/self-contradictory',
          'your 8' not in qk_text and 'your 9' not in qk_text and 'Player A pulls ahead' in qk_text, qk_text[:120])
    check('qk note accurate to data (9 beats 8, 7 never compared)',
          '9♦ beats the 8' in qk_text and '7♣' in qk_text and 'never even gets compared' in qk_text)
    page.click('#qk label[for="qk-w1"]')  # undo

    # ---------- q1 win state ----------
    for i in range(1, 6):
        page.click(f'#q1 label[for="q1-b{i}"]')
    page.wait_for_timeout(150)
    check('q1 win reveal shows', vis(page, '#q1 .reveal-win').startswith('block'), vis(page, '#q1 .reveal-win'))
    check('q1 wrong reveal suppressed on win', vis(page, '#q1 .reveal-wrong') == 'none|ZERO' or vis(page, '#q1 .reveal-wrong').startswith('none'))
    page.click('#q1 details.hand-reveal summary')
    page.wait_for_timeout(100)
    check('q1 hand-name reveal = Straight',
          page.evaluate("document.querySelector('#q1 .hand-name-big').textContent.trim()") == 'Straight')
    page.screenshot(path=str(OUT / 'fix-q1-win.png'))
    for i in range(1, 6):
        page.click(f'#q1 label[for="q1-b{i}"]')
    page.wait_for_timeout(100)

    # ---------- new prompt text ----------
    prompt = page.evaluate("document.querySelector('#q1 .q-prompt').textContent")
    check('prompt no longer promises "name the hand" as an action', 'then name the hand' not in prompt, prompt.strip())

    # ---------- trap reveal tap-agnostic ----------
    trap_wrong_ids = page.evaluate("""() => {
        const out = {};
        document.querySelectorAll('.q-trap').forEach(t => {
            out[t.id] = Array.from(t.querySelectorAll('.qcheck-wrong')).map(i => i.id);
        });
        return out; }""")
    print('trap wrong ids:', trap_wrong_ids)
    for tid, ids in trap_wrong_ids.items():
        for wid in ids:
            page.click(f'#{tid} label[for="{wid}"]')
            page.wait_for_timeout(80)
            txt = page.evaluate(f"document.querySelector('#{tid} .reveal-wrong').innerText")
            ok = vis(page, f'#{tid} .reveal-wrong').startswith('block')
            tapword = re.search(r'\btap', txt, re.I)
            check(f'{tid} reveal opens on wrong tap {wid}', ok)
            check(f'{tid} reveal text tap-agnostic (no "tap" wording)', tapword is None,
                  txt[max(0, tapword.start()-40):tapword.start()+40] if tapword else '')
            page.click(f'#{tid} label[for="{wid}"]')
            page.wait_for_timeout(60)
    t5 = page.evaluate("document.querySelector('#t5 .reveal-wrong').innerText")
    print('--- t5 reveal (tapped 4♦) ---\n' + t5 + '\n---')
    check('t5 still names the full house on the board', 'K♥ K♣ K♦ Q♠ Q♣' in t5)

    # ---------- full-house 3+2 bracket demo (learn mode) ----------
    page.click('label[for="mode-input-learn"]')
    page.wait_for_timeout(200)
    fh = page.evaluate("""() => {
        const d = document.querySelector('.fh-demo details.breakdown');
        if (!d) return null;
        d.open = true;
        return {labels: Array.from(d.querySelectorAll('.grp')).map(g => g.dataset.label),
                cards: d.querySelectorAll('.grp .brk-card').length,
                note: d.querySelector('.brk-note').textContent.trim()}; }""")
    check('full-house breakdown exists', fh is not None)
    check('full-house brackets are 3 + 2', fh and fh['labels'] == ['the 3 — three queens', 'the 2 — two eights'], fh)
    check('full-house breakdown = 5 cards', fh and fh['cards'] == 5, fh and fh['cards'])
    page.screenshot(path=str(OUT / 'fix-fullhouse-brackets.png'))

    # ---------- high-card tip (queen) ----------
    tip = page.evaluate("""() => Array.from(document.querySelectorAll('#hand-10 .note-tip p')).map(p=>p.textContent)[0]""")
    check('high-card tip includes queen in kicker order', 'queen' in tip, tip[-70:])

    # ---------- 360px overflow ----------
    m = br.new_context(viewport={'width': 360, 'height': 740}, is_mobile=True, has_touch=True)
    mp = m.new_page()
    mp.goto(BASE, wait_until='load')
    mp.wait_for_timeout(400)
    over = mp.evaluate("() => ({docW: document.documentElement.scrollWidth, winW: window.innerWidth})")
    check('360px no horizontal overflow', over['docW'] <= over['winW'] + 1, over)
    mp.click('label[for="tab-input-combine"]'); mp.click('label[for="mode-input-quiz"]')
    mp.wait_for_timeout(200)
    over2 = mp.evaluate("() => ({docW: document.documentElement.scrollWidth, winW: window.innerWidth})")
    check('360px quiz mode no overflow', over2['docW'] <= over2['winW'] + 1, over2)
    mh = mp.evaluate("""() => { const r = document.querySelector('.masthead h1').getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height), bottom: Math.round(r.bottom)}; }""")
    check('h1 fits masthead at 360px', mh['w'] <= 360 and mh['h'] < 120, mh)
    mp.screenshot(path=str(OUT / 'fix-360-h1.png'))
    m.close()

    check('console clean', not console and not errors, console[:3] + errors[:3])
    br.close()

print()
print('FAILURES:', fails if fails else 'none')
sys.exit(1 if fails else 0)
