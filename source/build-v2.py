#!/usr/bin/env python3
"""Generate poker-hands-v2.html programmatically.

Inputs (authoritative, never hand-transcribed into the HTML):
  /tmp/poker-hands/hands-content.json    — primer, hands[10], interaction{examples[5], mistakes[7]}, glossary
  /tmp/poker-hands/v2-quiz-content.json  — quiz[5], traps[7], seo{...}  (machine-verified by build-quiz.py)

Outputs:
  /tmp/poker-hands/v2/poker-hands-v2.html + /tmp/poker-hands/v2/poker-cards/ (52 SVGs)
  ~/dev/poker-hands-artifact/content/public/poker-hands-v2.html + poker-cards/ + registry-entry-v2.txt

v2 architecture: CSS-native-first. Tabs + learn/quiz mode are radio-hacks,
quiz state is checkbox-hack + :has() chains, expansions are <details>.
Inline JS at the bottom is optional enhancement only (hash + scroll).
"""
import json, html, os, re, shutil, datetime

HANDS = json.load(open('/tmp/poker-hands/hands-content.json'))
QV2 = json.load(open('/tmp/poker-hands/v2-quiz-content.json'))
CARDS_SRC = '/tmp/poker-hands/cards-opt3'
OUT_DIR = '/tmp/poker-hands/v2'
ARTIFACT = os.path.expanduser('~/dev/poker-hands-artifact')
DEPLOY_BASE = 'https://portfolio.jordanchristley.com/public/poker-hands-v2/'

SUITS = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
SUIT_SYM = {v: k for k, v in SUITS.items()}
SUIT_NAME = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
RANK_WORD = {'A': 'Ace', 'K': 'King', 'Q': 'Queen', 'J': 'Jack', '10': 'Ten',
             '9': 'Nine', '8': 'Eight', '7': 'Seven', '6': 'Six', '5': 'Five',
             '4': 'Four', '3': 'Three', '2': 'Two'}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VAL = {r: i + 2 for i, r in enumerate(RANKS)}


def e(s):
    return html.escape(str(s), quote=True)


def to_ascii(card):
    """'10♠' -> '10S'"""
    return card.strip()[:-1].strip() + SUITS[card.strip()[-1]]


def to_unicode(code):
    """'10S' -> '10♠'"""
    return code[:-1] + SUIT_SYM[code[-1]]


def parse(code):
    m = re.fullmatch(r'(10|[2-9]|J|Q|K|A)([SHDC])', code)
    assert m, f'bad card code: {code!r}'
    return m.group(1), m.group(2)


def card_name(code):
    rank, suit = parse(code)
    return f'{RANK_WORD[rank]} of {SUIT_NAME[SUIT_SYM[suit]]}'


def unicode_list(codes):
    return ' '.join(to_unicode(c) for c in codes)


def card_img(code, cls='', ring=False, dim=False, style='', eager=False):
    klass = 'card' + (f' {cls}' if cls else '')
    if ring:
        klass += ' counts'
    if dim:
        klass += ' dimmed'
    load = '' if eager else ' loading="lazy"'
    st = f' style="{style}"' if style else ''
    return (f'<img src="poker-cards/{code}.svg" alt="{e(card_name(code))}" '
            f'class="{klass}"{load} width="168" height="244"{st} decoding="async">')


def fan(cards, cls='', eager=False):
    n = len(cards)
    out = [f'<div class="fan {cls}">']
    for i, c in enumerate(cards):
        rot = (i - (n - 1) / 2) * 4.5
        lift = abs(i - (n - 1) / 2) * 3
        out.append(card_img(c, style=f'transform:rotate({rot:.1f}deg) translateY({lift:.0f}px);z-index:{i}',
                            eager=eager and i == 0))
    out.append('</div>')
    return ''.join(out)


# ---------------------------------------------------------------- assertions
assert len(QV2['quiz']) == 5 and len(QV2['traps']) == 7
for i, (ex, q) in enumerate(zip(HANDS['interaction']['examples'], QV2['quiz'])):
    assert [to_ascii(c) for c in ex['hole']] == q['hole'], (i, 'hole mismatch')
    assert [to_ascii(c) for c in ex['board']] == q['board'], (i, 'board mismatch')
    assert sorted(map(to_ascii, ex['best5'])) == sorted(q['best5']), (i, 'best5 mismatch')
for t in QV2['traps']:
    non_best = set(t['hole'] + t['board']) - set(t['correct_best5'])
    assert set(t['wrong_answer_cards']) <= non_best, t['id']  # bait cards are always non-best
all_cards = set()
for group in (QV2['quiz'], QV2['traps']):
    for ex in group:
        key = 'best5' if 'best5' in ex else 'correct_best5'
        all_cards |= set(ex['hole'] + ex['board'] + ex[key])
for h in HANDS['hands']:
    all_cards |= {to_ascii(c) for c in h['example_cards']}
missing = [c for c in all_cards if not os.path.exists(f'{CARDS_SRC}/{c}.svg')]
assert not missing, f'missing card SVGs: {missing}'

# ---------------------------------------------------------------- Tab 1
def tier_for(rank):
    return 'gold' if rank <= 3 else ('mid' if rank <= 6 else 'low')


def hand_block(h):
    rank = h['rank']
    tier = tier_for(rank)
    beats = h.get('beats_rank') or []
    chips = ''.join(f'<span class="chip">{e(b)}</span>' for b in beats)
    if not chips:
        chips = (f'<span class="chip chip-none">{"nothing &mdash; this is the top" if rank == 1 else "nothing &mdash; the weakest category"}</span>')
    name_cls = 'hand-name' + (' hand-name-top' if rank == 1 else '')
    return f'''
<article class="hand tier-{tier}" id="hand-{rank}">
  <div class="hand-rail">
    <span class="hand-rank">#{rank}</span>
    <span class="hand-rank-total">/10</span>
  </div>
  <div class="hand-body">
    <header class="hand-head">
      <h3 class="{name_cls}">{e(h['name'])}</h3>
      <div class="odds">
        <span class="odds-label">odds</span>
        <span class="odds-value">{e(h['odds'])}</span>
        <span class="odds-combos">{h['combos']:,} possible combinations</span>
      </div>
    </header>
    {fan([to_ascii(c) for c in h['example_cards']], cls='fan-hand', eager=(rank == 1))}
    <p class="definition">{e(h['definition'])}</p>
    <div class="beats">
      <span class="beats-label">what it beats</span>
      <div class="chips">{chips}</div>
    </div>
    <p class="why"><span class="why-label">why</span>{e(h['why'])}</p>
    <div class="notes">
      <div class="note note-tip">
        <span class="note-label">Beginner tip</span>
        <p>{e(h['beginner_tip'])}</p>
      </div>
      <div class="note note-story">
        <span class="note-label">How it happened</span>
        <p>{e(h['community_note'])}</p>
      </div>
    </div>
  </div>
</article>'''


hands_html = ''.join(hand_block(h) for h in HANDS['hands'])

# ---------------------------------------------------------------- breakdowns
def eval5_shape(codes):
    """Return ('straight'|'flush'|'straight_flush'|'ranked', info) for grouping."""
    vals = sorted((RANK_VAL[parse(c)[0]] for c in codes), reverse=True)
    suits = [parse(c)[1] for c in codes]
    is_flush = len(set(suits)) == 1
    uniq = sorted(set(vals), reverse=True)
    is_straight = len(uniq) == 5 and (uniq[0] - uniq[4] == 4 or uniq == [14, 5, 4, 3, 2])
    return is_flush, is_straight, suits[0]


def breakdown_groups(best5):
    """Group the best-5 for a CSS-bracket visual breakdown.
    Returns [(codes, label), ...] — biggest multiplicity groups first."""
    is_flush, is_straight, suit = eval5_shape(best5)
    if is_straight and is_flush:
        return [(best5, 'straight flush — five in a row, one suit')]
    if is_flush:
        return [(best5, f'all five {SUIT_NAME[SUIT_SYM[suit]]} — a flush')]
    if is_straight:
        return [(best5, 'five in a row — a straight')]
    by_rank = {}
    for c in best5:
        by_rank.setdefault(parse(c)[0], []).append(c)
    ordered = sorted(by_rank.items(), key=lambda kv: (len(kv[1]), RANK_VAL[kv[0]]), reverse=True)
    groups, kickers = [], []
    words = {2: 'two', 3: 'three'}
    for rank, cs in ordered:
        if len(cs) >= 2:
            label = (f'{"three of a kind" if len(cs) == 3 else "a pair"} — '
                     f'{words[len(cs)]} {RANK_WORD[rank].lower()}s')
            groups.append((cs, label))
        else:
            kickers.extend(cs)
    # full house is the only hand that splits into TWO groups (3 + 2) — label it as such
    if len(groups) == 2 and sorted(len(g[0]) for g in groups) == [2, 3]:
        g3 = next(g for g in groups if len(g[0]) == 3)
        g2 = next(g for g in groups if len(g[0]) == 2)
        groups = [(g3[0], f'the 3 — three {RANK_WORD[parse(g3[0][0])[0]].lower()}s'),
                  (g2[0], f'the 2 — two {RANK_WORD[parse(g2[0][0])[0]].lower()}s')]
    if kickers:
        groups.append((kickers, 'kickers — the best leftovers'))
    return groups


def breakdown_html(ex, hand_name):
    best5 = [to_ascii(c) for c in ex['best5']]
    remaining = list(best5)
    rows = []
    for codes, label in breakdown_groups(best5):
        cells = ''.join(
            card_img(c, cls='brk-card', ring=True,
                     style='transform:rotate(-1deg)') for c in codes)
        rows.append(f'<span class="grp" data-label="{e(label)}">'
                    f'<span class="grp-cards">{cells}</span></span>')
    discarded = [to_ascii(c) for c in ex['hole'] + ex['board'] if to_ascii(c) not in remaining]
    disc = ''
    if discarded:
        cells = ''.join(card_img(c, cls='brk-card', dim=True) for c in discarded)
        disc = (f'<div class="brk-discard"><span class="brk-discard-label">'
                f'discarded &mdash; not in your best 5</span>'
                f'<div class="brk-cards">{cells}</div></div>')
    return f'''
<details class="breakdown">
  <summary>See the breakdown</summary>
  <div class="brk-rows">{''.join(rows)}</div>
  {disc}
  <p class="brk-note">Your hand is these five cards: <strong>{e(hand_name.lower())}</strong> &mdash; {e(unicode_list(best5))}.</p>
</details>'''


def example_block(ex, idx, hand_name):
    hole = [to_ascii(c) for c in ex['hole']]
    board = [to_ascii(c) for c in ex['board']]
    best5 = [to_ascii(c) for c in ex['best5']]
    remaining = list(best5)
    hole_used = []
    for c in hole:
        used = c in remaining
        if used:
            remaining.remove(c)
        hole_used.append(used)
    board_used = []
    for c in board:
        used = c in remaining
        if used:
            remaining.remove(c)
        board_used.append(used)
    assert not remaining, (ex['title'], remaining)
    hole_cards = ''.join(
        card_img(c, cls='hero-card', ring=hole_used[i], dim=not hole_used[i],
                 style=f'transform:rotate({(i * 3 - 1.5):.1f}deg)')
        for i, c in enumerate(hole))
    board_cards = ''.join(card_img(c, ring=board_used[i], dim=not board_used[i]) for i, c in enumerate(board))
    return f'''
<section class="example">
  <h3 class="example-title"><span class="example-num">{idx}</span><span class="example-hand">{e(hand_name)}</span>&nbsp;&mdash;&nbsp;{e(ex['title'])}</h3>
  <div class="table-row">
    <div class="zone zone-hole">
      <span class="zone-label">Your hand &mdash; 2 hole cards</span>
      <div class="zone-cards">{hole_cards}</div>
    </div>
    <div class="zone zone-board">
      <span class="zone-label zone-label-board">Board &mdash; 5 community cards</span>
      <div class="zone-cards zone-cards-board">{board_cards}</div>
    </div>
  </div>
  <p class="legend"><span class="legend-ring"></span>outlined cards count toward your best 5 &nbsp;&middot;&nbsp; greyed cards are discarded</p>
  <p class="example-expl">{e(ex['explanation'])}</p>
  {breakdown_html(ex, hand_name)}
</section>'''


examples_html = ''.join(
    example_block(ex, i + 1, QV2['quiz'][i]['hand_name'])
    for i, ex in enumerate(HANDS['interaction']['examples']))

# full-house 3+2 bracket demo for learn mode — reuses the verified Full house example cards
FH_HAND = next(h for h in HANDS['hands'] if h['name'] == 'Full house')
FH_DEMO = breakdown_html({'best5': list(FH_HAND['example_cards']), 'hole': [], 'board': []},
                         FH_HAND['name'])

# ---------------------------------------------------------------- learn zone
P = HANDS['primer']
steps_html = ''.join(f'<li>{e(s)}</li>' for s in P['steps'])
primer_notes = ''.join(f'''
  <div class="primer-note">
    <span class="note-label">{label}</span>
    <p>{e(P[key])}</p>
  </div>''' for key, label in [
    ('card_order', 'Card order, low → high'),
    ('low_ace_note', 'The one ace exception'),
    ('suits_note', 'Suits are equal'),
    ('hand_is_exactly_five', 'Always exactly five'),
])
mistakes = ''.join(f'<li>{e(m)}</li>' for m in HANDS['interaction']['mistakes'])
glossary = ''.join(f'''
    <div class="term">
      <dt>{e(g['term'])}</dt>
      <dd>{e(g['definition'])}</dd>
    </div>''' for g in HANDS['glossary'])

learn_zone = f'''
<div class="mode-zone learn-zone">
  <div class="primer">
    <h2>{e(P['title'])}</h2>
    <p>{e(P['intro'])}</p>
    <ol class="primer-steps">{steps_html}</ol>
    <div class="primer-notes">{primer_notes}</div>
  </div>

  <h3 class="panel-sub">{e(HANDS['interaction']['title'])} &mdash; five worked examples, from needing both your cards to using neither.</h3>
  {examples_html}

  <aside class="fh-demo">
    <h3 class="panel-sub">The one hand with two brackets &mdash; a full house splits 3 + 2</h3>
    <p class="quiz-section-note">Every other hand breaks into a single matching group plus leftover kickers. A full house is the exception: three of one rank <em>and</em> a pair of another. Compare the triple first &mdash; the pair only matters when the triples tie.</p>
    {FH_DEMO}
  </aside>

  <aside class="mistakes">
    <h2>Seven beginner traps</h2>
    <p class="sub">If you remember nothing else from this page, remember these. Then switch to <strong>Quiz</strong> above and walk into all seven on purpose.</p>
    <ol>{mistakes}</ol>
  </aside>

  <section class="glossary">
    <h2>Glossary</h2>
    <dl>{glossary}
    </dl>
  </section>
</div>'''

# ---------------------------------------------------------------- quiz zone
QA_CSS = []  # per-question :has() rules


def qcards(codes, prefix, best5, wrong, hole_rot=False, cnt=None):
    """Render tappable quiz cards: hidden checkbox + label wrapping the card img.

    cnt is a shared {'b':0,'w':0} counter for the whole question so hole and
    board zones never collide on input ids."""
    if cnt is None:
        cnt = {'b': 0, 'w': 0}
    nb, nw = cnt['b'], cnt['w']
    rendered = []
    for c in codes:
        if c in best5:
            cnt['b'] += 1
            nb = cnt['b']
            cls, cid = 'is-best', f'{prefix}-b{nb}'
            chk = 'qcheck-best'
        else:
            cnt['w'] += 1
            nw = cnt['w']
            cls, cid = 'is-wrong', f'{prefix}-w{nw}'
            chk = 'qcheck-wrong'
        style = f'transform:rotate({((nb + nw - 3) * 1.5):.1f}deg)' if hole_rot else ''
        rendered.append(
            f'<span class="qcard {cls}">'
            f'<input type="checkbox" id="{cid}" class="sr-only qcheck {chk}" '
            f'aria-label="Select {e(card_name(c))}">'
            f'<label for="{cid}">{card_img(c, style=style)}</label></span>')
    return ''.join(rendered)


def question_css(qid, best_ids, wrong_count):
    wrong_sel = ''.join(f':has(#{qid}-w{i}:checked)' for i in range(1, wrong_count + 1))
    win_sel = ''.join(f':has(#{qid}-b{i}:checked)' for i in range(1, 6))
    QA_CSS.append(
        f'#{qid}:has(.qcheck-wrong:checked) .reveal-wrong, '
        f'#{qid}{win_sel}:not(:has(.qcheck-wrong:checked)) .reveal-win {{ display: block; }}\n'
        f'#{qid}:has(.qcheck-wrong:checked) .qcard.is-best label, '
        f'#{qid}{win_sel}:not(:has(.qcheck-wrong:checked)) .qcard.is-best label {{ outline-color: var(--green); }}\n'
        f'#{qid}:has(.qcheck-wrong:checked) .qcard.is-wrong label {{ outline-color: var(--red); }}'
    )


def quiz_question(q, n):
    qid = f'q{n}'
    hole, board, best5 = q['hole'], q['board'], q['best5']
    wrong = [c for c in hole + board if c not in best5]
    question_css(qid, None, len(wrong))
    cnt = {'b': 0, 'w': 0}
    hole_cards = qcards(hole, qid, best5, wrong, hole_rot=True, cnt=cnt)
    board_cards = qcards(board, qid, best5, wrong, cnt=cnt)
    assert cnt['b'] == 5, (qid, cnt)
    best_list = unicode_list(best5)
    return f'''
<section class="quiz-q" id="{qid}">
  <div class="q-head">
    <span class="q-num">Q{n}</span>
    <h4 class="q-title">{e(q['title'])}</h4>
  </div>
  <p class="q-prompt">{e(q['prompt'])}</p>
  <div class="table-row">
    <div class="zone zone-hole">
      <span class="zone-label">Your hand &mdash; 2 hole cards</span>
      <div class="zone-cards">{hole_cards}</div>
    </div>
    <div class="zone zone-board">
      <span class="zone-label zone-label-board">Board &mdash; 5 community cards</span>
      <div class="zone-cards zone-cards-board">{board_cards}</div>
    </div>
  </div>
  <p class="q-hint">Tap to select &middot; tap again to undo</p>
  <div class="reveal reveal-wrong">
    <span class="reveal-tag">Not quite</span>
    <p>{e(q['distractor_note'])}</p>
    <p class="reveal-best">Your best 5 is outlined in green above &mdash; deselect and try again.</p>
  </div>
  <div class="reveal reveal-win">
    <span class="reveal-tag">That&rsquo;s your best 5 of 7</span>
    <p>{best_list} &mdash; all five count.</p>
    <details class="hand-reveal">
      <summary>What hand is it?</summary>
      <p class="hand-name-big">{e(q['hand_name'])}</p>
    </details>
  </div>
</section>'''


def paired_question(a, b, n):
    """Kicker question: two hole lines, one shared board."""
    qid = 'qk'
    best5 = a['best5']                      # Player A's winning 5
    wrong = [c for c in a['hole'] + b['hole'] + a['board'] if c not in best5]
    question_css(qid, None, len(wrong))
    cnt = {'b': 0, 'w': 0}
    a_cards = qcards(a['hole'], qid, best5, wrong, hole_rot=True, cnt=cnt)
    b_cards = qcards(b['hole'], qid, best5, wrong, hole_rot=True, cnt=cnt)
    board_cards = qcards(a['board'], qid, best5, wrong, cnt=cnt)
    assert cnt['b'] == 5, (qid, cnt)
    assert a['board'] == b['board']
    fourth_a, fourth_b = a['best5'][3], b['best5'][3]
    # ONE coherent paragraph, written from the learner's table perspective.
    # (Never stitch a['distractor_note'] + b['distractor_note'] — "your" flipped players.)
    duel_note = a['distractor_note']
    return f'''
<section class="quiz-q q-paired" id="{qid}">
  <div class="q-head">
    <span class="q-num">Q{n}</span>
    <h4 class="q-title">One board, two players &mdash; who actually wins?</h4>
  </div>
  <p class="q-prompt">Both players pair the board&rsquo;s kings and both hold an ace. Tap Player A&rsquo;s 5 cards &mdash; the winning hand.</p>
  <div class="table-row">
    <div class="zone zone-hole zone-duel">
      <span class="zone-label">Player A &mdash; hole cards</span>
      <div class="zone-cards">{a_cards}</div>
      <span class="zone-label zone-label-b">Player B &mdash; hole cards</span>
      <div class="zone-cards">{b_cards}</div>
    </div>
    <div class="zone zone-board">
      <span class="zone-label zone-label-board">Board &mdash; 5 community cards, shared by both</span>
      <div class="zone-cards zone-cards-board">{board_cards}</div>
    </div>
  </div>
  <p class="q-hint">Tap to select &middot; tap again to undo</p>
  <div class="reveal reveal-wrong">
    <span class="reveal-tag">Not quite</span>
    <p>{e(duel_note)}</p>
    <p class="reveal-best">Player A&rsquo;s best 5 is outlined in green above &mdash; deselect and try again.</p>
  </div>
  <div class="reveal reveal-win">
    <span class="reveal-tag">Exactly &mdash; Player A wins</span>
    <p>{unicode_list(a['best5'])} beats Player B&rsquo;s {unicode_list(b['best5'])}.</p>
    <details class="hand-reveal">
      <summary>Show me the kicker ladder</summary>
      <p class="hand-name-big">{e(a['hand_name'])}</p>
      <p class="ladder">K&ndash;K&ndash;A is identical on both sides &mdash; then the fourth card decides: Player A&rsquo;s <strong>{to_unicode(fourth_a)}</strong> outranks Player B&rsquo;s <strong>{to_unicode(fourth_b)}</strong>. One kicker, the whole pot.</p>
    </details>
  </div>
</section>'''


MYTH_RE = re.compile(r'"([^"]+)"')


def trap_question(t, n, mistakes):
    qid = f't{n}'
    best5 = t['correct_best5']
    allc = t['hole'] + t['board']
    wrong = [c for c in allc if c not in best5]
    assert set(t['wrong_answer_cards']) <= set(wrong), t['id']  # bait cards are tappable wrongs
    question_css(qid, None, len(wrong))
    cnt = {'b': 0, 'w': 0}
    hole_cards = qcards(t['hole'], qid, best5, wrong, hole_rot=True, cnt=cnt)
    board_cards = qcards(t['board'], qid, best5, wrong, cnt=cnt)
    assert cnt['b'] == 5, (qid, cnt)
    myth = MYTH_RE.search(mistakes[t['mistake_ref']])
    myth_q = f'&ldquo;{e(myth.group(1))}&rdquo;' if myth else ''
    best_list = unicode_list(best5)
    return f'''
<section class="quiz-q q-trap" id="{qid}">
  <div class="q-head">
    <span class="q-num">Trap {n}/7</span>
    <h4 class="q-title sr-only">Beginner trap {n}</h4>
  </div>
  <p class="q-prompt">Tap the 5 cards you would play. What do you have?</p>
  <div class="table-row">
    <div class="zone zone-hole">
      <span class="zone-label">Your hand &mdash; 2 hole cards</span>
      <div class="zone-cards">{hole_cards}</div>
    </div>
    <div class="zone zone-board">
      <span class="zone-label zone-label-board">Board &mdash; 5 community cards</span>
      <div class="zone-cards zone-cards-board">{board_cards}</div>
    </div>
  </div>
  <p class="q-hint">Tap to select &middot; tap again to undo</p>
  <div class="reveal reveal-wrong">
    <span class="reveal-tag">You took the bait</span>
    <p class="bait-line"><s>{e(t['bait_title'])}</s></p>
    {f'<span class="note-label">Beginner mistake &middot; {myth_q}</span>' if myth_q else ''}
    <span class="note-label">The rule</span>
    <p>{e(t['trap_rule'])}</p>
    <span class="note-label">Why the bait fails</span>
    <p>{e(t['why_the_bait_fails'])}</p>
    <p class="reveal-best">Your best 5 (outlined in green above): {best_list} &mdash; <strong>{e(t['correct_hand_name'])}</strong></p>
  </div>
  <div class="reveal reveal-win">
    <span class="reveal-tag">You dodged the trap</span>
    <p>{best_list} &mdash; <strong>{e(t['correct_hand_name'])}</strong>. That is the best 5 of your 7.</p>
  </div>
  <details class="showme">
    <summary>Show me</summary>
    <div class="showme-body">
      <span class="note-label">The rule</span>
      <p>{e(t['trap_rule'])}</p>
      <span class="note-label">Why the bait fails</span>
      <p>{e(t['why_the_bait_fails'])}</p>
      <div class="showme-best">
        {fan(best5, cls='fan-brk')}
        <p class="showme-name">{e(t['correct_hand_name'])} &mdash; {best_list}</p>
      </div>
    </div>
  </details>
</section>'''


warmups = ''.join(quiz_question(QV2['quiz'][0], 1)
                  + quiz_question(QV2['quiz'][1], 2)
                  + quiz_question(QV2['quiz'][2], 3)
                  + paired_question(QV2['quiz'][3], QV2['quiz'][4], 4))
trapz = ''.join(trap_question(t, i + 1, HANDS['interaction']['mistakes'])
                for i, t in enumerate(QV2['traps']))

quiz_zone = f'''
<div class="mode-zone quiz-zone">
  <h2 class="quiz-h2">Test yourself</h2>
  <p class="panel-intro quiz-intro"><strong>Tap the cards, not the answers.</strong> Every deal below is real: pick the 5 cards that make your best hand out of your 7. Get it wrong and the table flips the lesson on you; get all 5 right and the hand reveals itself. First four are warm-ups &mdash; the last seven are the classic beginner traps, served raw.</p>
  <p class="teacher-note">Coaching tip: let them fall for each trap before revealing the rule &mdash; the mistake is the lesson.</p>
  <p class="no-has-note">Heads up: this browser doesn&rsquo;t support the <code>:has()</code> CSS rule the tap quiz runs on, so every question below is shown as a static answer sheet. Update to Chrome 105+, Safari 15.4+ or Firefox 121+ for the interactive version.</p>

  <h3 class="quiz-section">Warm-up &mdash; four spots</h3>
  {warmups}

  <h3 class="quiz-section">The seven beginner traps &mdash; no titles, no mercy</h3>
  <p class="quiz-section-note">You see only hole cards and board, exactly like a real hand. Tap what you believe &mdash; the teaching arrives the moment you fall for it. In a hurry? Every trap has a &ldquo;Show me&rdquo; link.</p>
  {trapz}
</div>'''

# ---------------------------------------------------------------- CSS
BASE_CSS = open('/tmp/poker-hands/v2-base.css').read()
V2_CSS = open('/tmp/poker-hands/v2-extra.css').read()

# ---------------------------------------------------------------- SEO head
seo = QV2['seo']
jsonld = json.dumps(seo['json_ld'], ensure_ascii=False).replace('<', '\\u003c')
desc = seo['meta_description']
title_tag = seo['title_tag']

page = f'''<!DOCTYPE html>
<html lang="en" data-version="v2">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title_tag)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{DEPLOY_BASE}">
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%20100%20100'%3E%3Cpath%20d='M50%2012C50%2012%2022%2036%2022%2054C22%2063%2028%2069%2036%2069C41%2069%2045%2067%2047%2064C46%2074%2042%2082%2035%2088L65%2088C58%2082%2054%2074%2053%2064C55%2067%2059%2069%2064%2069C72%2069%2078%2063%2078%2054C78%2036%2050%2012%2050%2012Z'%20fill='%23FFD700'/%3E%3C/svg%3E">
<meta property="og:title" content="{e(title_tag)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{DEPLOY_BASE}">
<meta property="og:site_name" content="Poker Hands, Decoded">
<meta property="og:image" content="{DEPLOY_BASE}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Poker Hands, Decoded — hand rankings and a tap quiz for beginners">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title_tag)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DEPLOY_BASE}og-image.png">
<script type="application/ld+json">{jsonld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
{BASE_CSS}

/* ===== v2 additions ===== */
{V2_CSS}

/* ===== per-question quiz state (:has chains, generated) ===== */
{chr(10).join(QA_CSS)}
</style>
</head>
<body>

<input type="radio" name="ph-tab" id="tab-input-rankings" class="sr-only" checked>
<input type="radio" name="ph-tab" id="tab-input-combine" class="sr-only">

<header class="masthead">
  <div class="masthead-inner">
    <p class="kicker">Texas Hold&rsquo;em &middot; Beginner Series</p>
    <h1>Poker Hands for Beginners, <em>Decoded</em></h1>
    <nav class="tabbar" aria-label="Sections">
      <label class="tab" for="tab-input-rankings" id="tab-rankings"><span class="tab-num">01</span>Hand Rankings</label>
      <label class="tab" for="tab-input-combine" id="tab-combine"><span class="tab-num">02</span>How Cards Combine</label>
    </nav>
  </div>
</header>

<main class="wrap">

<section class="tab-panel" id="panel-rankings" aria-labelledby="tab-rankings">
  <h2 class="sr-only">Hand rankings &mdash; all ten poker hands, strongest first</h2>
  <p class="panel-intro">All ten poker hands, <strong>strongest first</strong> &mdash; a royal flush at the top, a whiffed high card at the bottom. Every example below is a real five-card hand, shown with real cards. Odds are per dealt hand.</p>
  {hands_html}
</section>

<section class="tab-panel" id="panel-combine" aria-labelledby="tab-combine">
  <input type="radio" name="ph-mode" id="mode-input-learn" class="sr-only" checked>
  <input type="radio" name="ph-mode" id="mode-input-quiz" class="sr-only">
  <h2 class="sr-only">How your hole cards and the community cards combine &mdash; learn, then quiz yourself</h2>
  <nav class="modebar" aria-label="Learn or quiz">
    <span class="modebar-kicker">This tab</span>
    <label class="mode-btn" for="mode-input-learn">Learn</label>
    <label class="mode-btn" for="mode-input-quiz">Quiz</label>
  </nav>
  {learn_zone}
  {quiz_zone}
</section>

<footer>
  <span>Poker Hands, Decoded &middot; v2 &mdash; learn by doing</span>
  <span>Card art: Vector Playing Cards (public domain)</span>
</footer>
</main>

<script>
/* Optional progressive enhancement only — every feature above works with this stripped. */
(function () {{
  var labels = document.querySelectorAll('label.tab');
  labels.forEach(function (l) {{
    l.addEventListener('click', function () {{
      setTimeout(function () {{
        var t = document.querySelector('input[name="ph-tab"]:checked');
        if (t && history.replaceState) history.replaceState(null, '', '#' + t.id.replace('tab-input-', ''));
        window.scrollTo(0, 0);
      }}, 0);
    }});
  }});
  var h = (location.hash || '').replace('#', '');
  if (h === 'combine') {{ var c = document.getElementById('tab-input-combine'); if (c) c.checked = true; }}
}})();
</script>
</body>
</html>
'''

# ---------------------------------------------------------------- id uniqueness
ids = re.findall(r'id="([^"]+)"', page)
dups = sorted({i for i in ids if ids.count(i) > 1})
assert not dups, f'duplicate ids: {dups}'

# ---------------------------------------------------------------- write
os.makedirs(f'{OUT_DIR}/poker-cards', exist_ok=True)
with open(f'{OUT_DIR}/poker-hands-v2.html', 'w') as f:
    f.write(page)
for fn in os.listdir(CARDS_SRC):
    if fn.endswith('.svg'):
        shutil.copy2(f'{CARDS_SRC}/{fn}', f'{OUT_DIR}/poker-cards/{fn}')

# artifacts-skill-shaped copy for the Mac merge
os.makedirs(f'{ARTIFACT}/content/public/poker-cards', exist_ok=True)
shutil.copy2(f'{OUT_DIR}/poker-hands-v2.html', f'{ARTIFACT}/content/public/poker-hands-v2.html')
for fn in os.listdir(f'{OUT_DIR}/poker-cards'):
    shutil.copy2(f'{OUT_DIR}/poker-cards/{fn}', f'{ARTIFACT}/content/public/poker-cards/{fn}')
# social card (1200x630 PNG) — deployed at {DEPLOY_BASE}og-image.png
og_src = f'{OUT_DIR}/og-image.png'
if os.path.exists(og_src):
    os.makedirs(f'{ARTIFACT}/content/public/poker-hands-v2', exist_ok=True)
    shutil.copy2(og_src, f'{ARTIFACT}/content/public/poker-hands-v2/og-image.png')

registry = f'''# registry entry v2 — for the portfolio-next / Mac merge.
# shape mirrors content/registry-entry.txt (v1). Merge both; v1 stays live.
'poker-hands-v2': {{
    slug: 'poker-hands-v2',
    tier: 'public',
    title: {title_tag!r},
    description:
      {desc!r},
    tag: 'Tutorial',
    published: '{datetime.date.today().isoformat()}',
    author: 'Jordan Christley',
    jsonLd: {{
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: {title_tag!r},
      description:
        {desc!r},
      author: {{
        '@type': 'Person',
        name: 'Jordan Christley',
      }},
      datePublished: '{datetime.date.today().isoformat()}',
    }},
    # page-level JSON-LD injected verbatim by build-v2.py (FAQPage, 8 Q&As):
    faqJsonLd: {json.dumps(seo['json_ld'], indent=6, ensure_ascii=False)},
}},
'''
with open(f'{ARTIFACT}/content/registry-entry-v2.txt', 'w') as f:
    f.write(registry)

print(f'wrote {OUT_DIR}/poker-hands-v2.html ({len(page)} bytes)')
print(f'cards: {len([f for f in os.listdir(f"{OUT_DIR}/poker-cards") if f.endswith(".svg")])} SVGs')
print(f'quiz questions: 4 warm-ups (3 + 1 paired) + 7 traps = 11 blocks, 12 verified examples')
print(f'QA css rules generated: {len(QA_CSS)}')
