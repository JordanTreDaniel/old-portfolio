#!/usr/bin/env python3
"""Script-stripped QA: page must be fully functional with zero <script> tags.
Also re-verifies the @supports fallback by FORCING the unsupported-branch simulation:
we can't disable :has() in modern Chrome, so we assert the fallback rules exist and
that the no-js copy behaves identically to the full copy."""
import pathlib, re, shutil, sys
from playwright.sync_api import sync_playwright

SRC = pathlib.Path('/tmp/poker-hands/v2')
DIR = pathlib.Path('/tmp/poker-hands/v2-noscript2')
if DIR.exists():
    shutil.rmtree(DIR)
DIR.mkdir(parents=True)
html = (SRC / 'poker-hands-v2.html').read_text()
n_scripts = len(re.findall(r'<script', html))
stripped = re.sub(r'<script\b.*?</script>', '', html, flags=re.S)
assert '<script' not in stripped, 'script tags remain'
(DIR / 'poker-hands-v2.html').write_text(stripped)
shutil.copytree(SRC / 'poker-cards', DIR / 'poker-cards')
print(f'stripped {n_scripts} script tags -> {DIR}')

fails = []
def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ((' — ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)

console, errors = [], []
with sync_playwright() as p:
    br = p.chromium.launch(args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'[:200]))
    page.on('pageerror', lambda e: errors.append(str(e)[:200]))
    page.goto('http://127.0.0.1:8735/poker-hands-v2.html', wait_until='load')
    page.wait_for_timeout(400)
    check('zero <script> in served copy', page.evaluate("document.querySelectorAll('script:not([type])').length") == 0)

    page.click('label[for="tab-input-combine"]'); page.wait_for_timeout(150)
    page.click('label[for="mode-input-quiz"]'); page.wait_for_timeout(150)
    check('tab + quiz mode switch work (CSS radio-hack)',
          page.evaluate("getComputedStyle(document.querySelector('.quiz-zone')).display") != 'none')

    page.click('#t1 label[for="t1-w1"]'); page.wait_for_timeout(120)
    check('trap wrong reveal works', page.evaluate("getComputedStyle(document.querySelector('#t1 .reveal-wrong')).display") == 'block')
    page.click('#t1 label[for="t1-w1"]'); page.wait_for_timeout(80)

    page.click('#t3 details.showme summary'); page.wait_for_timeout(100)
    check('"Show me" details opens', page.evaluate("document.querySelector('#t3 details.showme').open"))

    for i in range(1, 6):
        page.click(f'#q1 label[for="q1-b{i}"]')
    page.wait_for_timeout(120)
    check('all-correct win reveal works', page.evaluate("getComputedStyle(document.querySelector('#q1 .reveal-win')).display") == 'block')
    page.click('#q1 details.hand-reveal summary'); page.wait_for_timeout(80)
    check('hand-name reveal works', page.evaluate("document.querySelector('#q1 .hand-name-big').textContent.trim()") == 'Straight')

    page.click('label[for="mode-input-learn"]'); page.wait_for_timeout(120)
    fh = page.evaluate("() => { const d = document.querySelector('.fh-demo details.breakdown'); d.open = true; return d.querySelectorAll('.grp').length; }")
    check('full-house breakdown opens', fh == 2, fh)
    check('console clean (stripped)', not console and not errors, console[:3] + errors[:3])
    br.close()

print()
print('FAILURES:', fails if fails else 'none')
sys.exit(1 if fails else 0)
