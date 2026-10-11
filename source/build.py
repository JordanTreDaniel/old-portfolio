#!/usr/bin/env python3
"""Generate poker-hands.html from hands-content.json (authoritative content)."""
import json, html

D = json.load(open('/tmp/poker-hands/hands-content.json'))
SUITS = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
SUIT_NAME = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
RANK_WORD = {'A': 'Ace', 'K': 'King', 'Q': 'Queen', 'J': 'Jack', '10': 'Ten',
             '9': 'Nine', '8': 'Eight', '7': 'Seven', '6': 'Six', '5': 'Five',
             '4': 'Four', '3': 'Three', '2': 'Two'}
HAND_NAMES = [h['name'] for h in D['hands']]


def code(card):
    card = card.strip()
    return card[:-1].strip() + SUITS[card[-1]]


def e(s):
    return html.escape(s, quote=True)


def card_name(card):
    card = card.strip()
    rank, suit = card[:-1].strip(), card[-1]
    return f"{RANK_WORD.get(rank, rank)} of {SUIT_NAME[suit]}"


def card_img(card, cls='', ring=False, dim=False, style=''):
    """Render one card as an <img> pointing at the optimized SVG."""
    c = code(card)
    klass = 'card' + (' ' + cls if cls else '')
    if ring:
        klass += ' counts'
    if dim:
        klass += ' dimmed'
    style_attr = f' style="{style}"' if style else ''
    return (f'<img src="poker-cards/{c}.svg" alt="{e(card_name(card))}" '
            f'class="{klass}" loading="lazy" width="168" height="244"{style_attr}>')


def fan(cards, cls='', ring_fn=None, dim_fn=None):
    """A fanned row of cards with slight rotation."""
    n = len(cards)
    out = [f'<div class="fan {cls}">']
    for i, c in enumerate(cards):
        rot = (i - (n - 1) / 2) * 4.5
        lift = abs(i - (n - 1) / 2) * 3
        style = f'transform:rotate({rot:.1f}deg) translateY({lift:.0f}px);z-index:{i}'
        out.append(card_img(c, ring=ring_fn(c, i) if ring_fn else False,
                            dim=dim_fn(c, i) if dim_fn else False, style=style))
    out.append('</div>')
    return ''.join(out)


# ---------------------------------------------------------------- Tab 1: hands
def tier_for(rank):
    if rank <= 3:
        return 'gold'
    if rank <= 6:
        return 'mid'
    return 'low'


def hand_block(h):
    rank = h['rank']
    tier = tier_for(rank)
    beats = h.get('beats_rank') or []
    chips = ''.join(f'<span class="chip">{e(b)}</span>' for b in beats)
    if not chips:
        chip_text = ('nothing &mdash; this is the top' if rank == 1
                     else 'nothing &mdash; the weakest category')
        chips = f'<span class="chip chip-none">{chip_text}</span>'
    odds = e(h['odds'])
    combos = h['combos']
    combos_s = f'{combos:,}'
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
        <span class="odds-value">{odds}</span>
        <span class="odds-combos">{combos_s} possible combinations</span>
      </div>
    </header>
    {fan(h['example_cards'], cls='fan-hand')}
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


hands_html = ''.join(hand_block(h) for h in D['hands'])

# ---------------------------------------------------------------- Tab 2: combine
P = D['primer']
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


def split_source(hole, best5):
    """Return (hole_used_flags, board_used_flags) via multiset matching, hole first."""
    remaining = list(best5)
    hole_used = []
    for c in hole:
        if c in remaining:
            remaining.remove(c)
            hole_used.append(True)
        else:
            hole_used.append(False)
    board_used = [c in remaining for c in board_placeholder(hole, best5)]
    return hole_used, board_used


def board_placeholder(hole, best5):
    raise RuntimeError


def example_block(ex, idx):
    hole, board, best5 = ex['hole'], ex['board'], ex['best5']
    # multiset match: hole takes priority, then board
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
    board_cards = ''.join(
        card_img(c, ring=board_used[i], dim=not board_used[i])
        for i, c in enumerate(board))
    return f'''
<section class="example">
  <h3 class="example-title"><span class="example-num">{idx}</span>{e(ex['title'])}</h3>
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
  <p class="legend"><span class="legend-ring"></span>outlined cards count toward your best 5 &nbsp;&middot;&nbsp; <span class="legend-dim">greyed cards are discarded</span></p>
  <p class="example-expl">{e(ex['explanation'])}</p>
</section>'''


examples_html = ''.join(example_block(ex, i + 1)
                        for i, ex in enumerate(D['interaction']['examples']))

mistakes = ''.join(f'<li>{e(m)}</li>' for m in D['interaction']['mistakes'])

glossary = ''.join(f'''
    <div class="term">
      <dt>{e(g['term'])}</dt>
      <dd>{e(g['definition'])}</dd>
    </div>''' for g in D['glossary'])

# ---------------------------------------------------------------- page
CSS = """
:root {
  --bg: #0a0a0a; --bg-card: #141414; --bg-card-alt: #1a1a1a;
  --pink: #FF1493; --cyan: #00E5FF; --gold: #FFD700; --green: #00E676;
  --red: #FF5252; --orange: #FF9100;
  --text: #e8e6e1; --text-dim: #9a968e; --text-faint: #625e57;
  --line: #262421; --line-soft: #1d1b19;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg); color: var(--text);
  font-family: var(--font-body); font-size: 16px; line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
img { display: block; }

/* ---------- header + tabs ---------- */
.masthead {
  position: sticky; top: 0; z-index: 100;
  background: rgba(10,10,10,.94);
  border-bottom: 1px solid var(--line);
  backdrop-filter: saturate(140%) blur(2px);
}
.masthead-inner {
  max-width: 1080px; margin: 0 auto; padding: 18px 24px 0;
}
.masthead h1 {
  font-family: var(--font-display); font-weight: 700;
  font-size: clamp(1.5rem, 3.4vw, 2.15rem); letter-spacing: .01em;
}
.masthead h1 em {
  font-style: italic;
  background: linear-gradient(100deg, var(--gold), var(--pink));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.masthead .kicker {
  font-family: var(--font-mono); font-size: .68rem; letter-spacing: .22em;
  text-transform: uppercase; color: var(--text-dim); margin-bottom: 4px;
}
.tabbar { display: flex; gap: 4px; margin-top: 14px; }
.tab {
  appearance: none; background: none; border: none; cursor: pointer;
  font-family: var(--font-mono); font-size: .8rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--text-dim);
  padding: 12px 18px 13px; border-bottom: 2px solid transparent;
  transition: color .18s, border-color .18s;
}
.tab:hover { color: var(--text); }
.tab[aria-selected="true"] { color: var(--gold); border-bottom-color: var(--gold); }
.tab .tab-num { color: var(--text-faint); margin-right: 7px; }
.tab[aria-selected="true"] .tab-num { color: var(--gold); }

.wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px 96px; }
.tab-panel { display: none; }
.tab-panel.active { display: block; animation: rise .35s ease both; }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

.panel-intro {
  padding: 30px 0 8px; color: var(--text-dim); font-size: .95rem;
  max-width: 62ch;
}
.panel-intro strong { color: var(--text); font-weight: 600; }

/* ---------- cards ---------- */
.fan { display: flex; align-items: flex-end; justify-content: center; padding: 18px 8px 26px; }
.card {
  width: auto; height: 118px; border-radius: 8px;
  filter: drop-shadow(0 8px 16px rgba(0,0,0,.55)) drop-shadow(0 1px 2px rgba(0,0,0,.6));
  transition: transform .25s ease, filter .25s ease, opacity .25s ease;
}
.fan-hand .card { margin: 0 -13px; }
.fan-hand .card:hover { transform: translateY(-8px) rotate(0deg) !important; z-index: 30; }

/* ---------- hand entries ---------- */
.hand {
  display: grid; grid-template-columns: 88px 1fr; gap: 0 20px;
  border-top: 1px solid var(--line); padding: 44px 0 48px;
}
.hand-rail {
  font-family: var(--font-mono); text-align: center; padding-top: 4px;
  position: sticky; top: 130px; align-self: start;
}
.hand-rank { font-size: 1.9rem; font-weight: 700; color: var(--text-faint); }
.hand-rank-total { display: block; font-size: .72rem; color: var(--text-faint); letter-spacing: .1em; }
.hand-head {
  display: flex; flex-wrap: wrap; align-items: baseline;
  justify-content: space-between; gap: 10px 24px; margin-bottom: 2px;
}
.hand-name {
  font-family: var(--font-display); font-weight: 700;
  font-size: 1.6rem; letter-spacing: .01em;
}
.odds { text-align: right; font-family: var(--font-mono); }
.odds-label {
  display: block; font-size: .6rem; letter-spacing: .24em;
  text-transform: uppercase; color: var(--text-faint);
}
.odds-value { font-size: 1.05rem; color: var(--cyan); }
.odds-combos { display: block; font-size: .66rem; color: var(--text-faint); }
.definition { max-width: 66ch; color: var(--text); font-size: .97rem; margin-top: 14px; }

.beats { margin-top: 18px; }
.beats-label, .note-label, .why-label {
  display: block; font-family: var(--font-mono); font-size: .6rem;
  letter-spacing: .24em; text-transform: uppercase; color: var(--text-faint);
  margin-bottom: 7px;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-family: var(--font-mono); font-size: .68rem; padding: 3px 10px;
  border: 1px solid var(--line); border-radius: 999px; color: var(--text-dim);
  background: var(--bg-card);
}
.chip-none { color: var(--gold); border-color: rgba(255,215,0,.35); }
.why { margin-top: 18px; max-width: 72ch; font-size: .92rem; color: var(--text-dim); }
.notes { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 22px; }
.note { background: var(--bg-card); border: 1px solid var(--line-soft); padding: 14px 16px; }
.note p { font-size: .85rem; color: var(--text-dim); }
.note-tip { border-left: 2px solid var(--green); }
.note-story { border-left: 2px solid var(--pink); }

/* tier emphasis: strongest hands get more visual weight */
.tier-gold { border-top-color: rgba(255,215,0,.5); }
.tier-gold .hand-rank { color: var(--gold); font-size: 2.5rem; }
.tier-gold .hand-rank-total { color: rgba(255,215,0,.55); }
.tier-gold .card { height: 152px; }
.tier-gold .hand-name { font-size: 2.2rem; }
.tier-gold .hand-name-top {
  background: linear-gradient(95deg, var(--gold) 20%, #fff2b0 60%, var(--gold));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.tier-gold .odds-value { color: var(--gold); font-size: 1.2rem; }
.tier-gold .definition { font-size: 1.02rem; }
#hand-1 { background: linear-gradient(180deg, rgba(255,215,0,.05), transparent 340px); }
.tier-mid .hand-rank { color: var(--text-dim); font-size: 1.7rem; }
.tier-mid .card { height: 128px; }
.tier-low .card { height: 100px; }
.tier-low .hand-name { font-size: 1.3rem; color: var(--text-dim); }
.tier-low .hand-rank { font-size: 1.45rem; }
.tier-low .definition, .tier-low .why { font-size: .88rem; color: var(--text-dim); }
.tier-low .notes { margin-top: 16px; }

/* ---------- primer ---------- */
.primer {
  margin-top: 30px; background: var(--bg-card); border: 1px solid var(--line);
  padding: 30px 32px 26px; position: relative; overflow: hidden;
}
.primer::before {
  content: ''; position: absolute; inset: 0 auto 0 0; width: 3px;
  background: linear-gradient(180deg, var(--gold), var(--pink));
}
.primer h2 {
  font-family: var(--font-display); font-size: 1.55rem; font-weight: 700;
  margin-bottom: 8px;
}
.primer > p { color: var(--text-dim); max-width: 70ch; font-size: .95rem; }
.primer-steps { list-style: none; counter-reset: step; margin: 20px 0 6px; display: grid; gap: 10px; }
.primer-steps li {
  counter-increment: step; position: relative; padding-left: 44px;
  font-size: .93rem; color: var(--text);
}
.primer-steps li::before {
  content: counter(step); position: absolute; left: 0; top: 1px;
  width: 28px; height: 28px; border-radius: 50%;
  border: 1px solid var(--gold); color: var(--gold);
  font-family: var(--font-mono); font-size: .75rem;
  display: flex; align-items: center; justify-content: center;
}
.primer-notes { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 20px; }
.primer-note { background: var(--bg-card-alt); padding: 13px 15px; border: 1px solid var(--line-soft); }
.primer-note p { font-size: .84rem; color: var(--text-dim); }

/* ---------- interaction examples ---------- */
.example { border-top: 1px solid var(--line); padding: 40px 0 44px; }
.example-title {
  font-family: var(--font-display); font-size: 1.35rem; font-weight: 700;
  display: flex; gap: 14px; align-items: baseline; max-width: 74ch;
}
.example-num {
  font-family: var(--font-mono); font-size: .7rem; color: var(--bg);
  background: var(--cyan); padding: 3px 9px; border-radius: 3px;
  flex: none; transform: translateY(-2px);
}
.table-row {
  display: grid; grid-template-columns: auto 1fr; gap: 28px;
  margin-top: 22px; align-items: start;
}
.zone-label {
  display: block; font-family: var(--font-mono); font-size: .62rem;
  letter-spacing: .2em; text-transform: uppercase; color: var(--gold);
  margin-bottom: 12px;
}
.zone-label-board { color: var(--cyan); }
.zone-cards { display: flex; gap: 8px; align-items: flex-end; }
.zone-hole {
  padding: 16px 20px 8px; background: var(--bg-card);
  border: 1px solid var(--line); border-radius: 10px;
}
.zone-hole .card { height: 128px; }
.zone-board {
  padding: 16px 20px 8px; background: var(--bg-card-alt);
  border: 1px dashed var(--line); border-radius: 10px;
}
.zone-board .card { height: 106px; }
.card.counts {
  outline: 2px solid var(--green); outline-offset: 3px; border-radius: 8px;
}
.card.dimmed { opacity: .22; filter: grayscale(1) drop-shadow(0 4px 8px rgba(0,0,0,.4)); }
.legend {
  margin-top: 16px; font-family: var(--font-mono); font-size: .68rem;
  color: var(--text-faint); display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.legend-ring {
  display: inline-block; width: 14px; height: 10px;
  outline: 2px solid var(--green); outline-offset: 2px; border-radius: 2px;
}
.example-expl { margin-top: 14px; max-width: 78ch; font-size: .93rem; color: var(--text-dim); }

/* ---------- mistakes callout ---------- */
.mistakes {
  margin-top: 44px; background: var(--bg-card);
  border: 1px solid var(--line); border-left: 3px solid var(--red);
  padding: 28px 32px;
}
.mistakes h2 {
  font-family: var(--font-display); font-size: 1.4rem; margin-bottom: 4px;
}
.mistakes .sub { color: var(--text-dim); font-size: .88rem; margin-bottom: 18px; }
.mistakes ol { list-style: none; counter-reset: myth; display: grid; gap: 13px; }
.mistakes li {
  counter-increment: myth; position: relative; padding-left: 40px;
  font-size: .9rem; color: var(--text-dim);
}
.mistakes li::before {
  content: '✗'; position: absolute; left: 6px; top: 0;
  color: var(--red); font-weight: 700; font-size: .95rem;
}
.mistakes li em { color: var(--text); font-style: italic; }

/* ---------- glossary ---------- */
.glossary { margin-top: 44px; }
.glossary h2 {
  font-family: var(--font-display); font-size: 1.4rem; margin-bottom: 18px;
}
.glossary dl { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--line); border: 1px solid var(--line); }
.term { background: var(--bg); padding: 14px 18px; }
.term dt {
  font-family: var(--font-mono); font-size: .74rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--gold); margin-bottom: 5px;
}
.term dd { font-size: .84rem; color: var(--text-dim); }

footer {
  border-top: 1px solid var(--line); margin-top: 70px; padding-top: 22px;
  font-family: var(--font-mono); font-size: .68rem; color: var(--text-faint);
  display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap;
}

/* ---------- responsive ---------- */
@media (max-width: 860px) {
  .hand { grid-template-columns: 1fr; padding: 34px 0 38px; }
  .hand-rail { position: static; text-align: left; margin-bottom: 6px; }
  .hand-rank { font-size: 1.4rem; }
  .hand-rank-total { display: inline; margin-left: 4px; }
  .tier-gold .hand-rank { font-size: 1.7rem; }
  .table-row { grid-template-columns: 1fr; gap: 18px; }
  .notes, .primer-notes, .glossary dl { grid-template-columns: 1fr; }
  .card { height: 92px; }
  .tier-gold .card { height: 108px; }
  .tier-mid .card { height: 98px; }
  .tier-low .card { height: 82px; }
  .zone-hole .card { height: 104px; }
  .zone-board .card { height: 86px; }
  .zone-cards { flex-wrap: wrap; }
  .odds { text-align: left; }
  .masthead-inner { padding: 14px 16px 0; }
  .wrap { padding: 0 16px 72px; }
  .tab { padding: 11px 12px; font-size: .72rem; }
  .primer, .mistakes { padding: 22px 18px; }
}
"""

JS = """
(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-panel'));
  function activate(id, push) {
    tabs.forEach(function (t) {
      t.setAttribute('aria-selected', String(t.dataset.tab === id));
    });
    panels.forEach(function (p) {
      p.classList.toggle('active', p.dataset.panel === id);
    });
    if (push && history.replaceState) history.replaceState(null, '', '#' + id);
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { activate(t.dataset.tab, true); });
  });
  var initial = (location.hash || '').replace('#', '');
  if (initial === 'combine' || initial === 'rankings') activate(initial, false);
})();
"""

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poker Hands, Decoded &mdash; A Beginner&rsquo;s Guide to Texas Hold&rsquo;em</title>
<meta name="description" content="Learn poker hand rankings from the royal flush down to high card, and how your two hole cards combine with the five community cards to make the best 5 of 7. Plain English, real examples, real cards.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <p class="kicker">Texas Hold&rsquo;em &middot; Beginner Series</p>
    <h1>Poker Hands, <em>Decoded</em></h1>
    <nav class="tabbar" role="tablist" aria-label="Sections">
      <button class="tab" role="tab" data-tab="rankings" aria-selected="true" aria-controls="panel-rankings" id="tab-rankings">
        <span class="tab-num">01</span>Hand Rankings</button>
      <button class="tab" role="tab" data-tab="combine" aria-selected="false" aria-controls="panel-combine" id="tab-combine">
        <span class="tab-num">02</span>How Cards Combine</button>
    </nav>
  </div>
</header>

<main class="wrap">

<section class="tab-panel active" data-panel="rankings" role="tabpanel" aria-labelledby="tab-rankings">
  <p class="panel-intro">All ten poker hands, <strong>strongest first</strong> &mdash; a royal flush at the top, a whiffed high card at the bottom. Every example below is a real five-card hand, shown with real cards. Odds are per dealt hand.</p>
  {hands_html}
</section>

<section class="tab-panel" data-panel="combine" role="tabpanel" aria-labelledby="tab-combine">
  <div class="primer">
    <h2>{e(P['title'])}</h2>
    <p>{e(P['intro'])}</p>
    <ol class="primer-steps">{steps_html}</ol>
    <div class="primer-notes">{primer_notes}</div>
  </div>

  <p class="panel-intro" style="padding-top:36px">{e(D['interaction']['title'])} &mdash; five worked examples, from needing both your cards to using neither.</p>

  {examples_html}

  <aside class="mistakes">
    <h2>Seven beginner traps</h2>
    <p class="sub">If you remember nothing else from this page, remember these.</p>
    <ol>{mistakes}</ol>
  </aside>

  <section class="glossary">
    <h2>Glossary</h2>
    <dl>{glossary}
    </dl>
  </section>
</section>

<footer>
  <span>Poker Hands, Decoded</span>
  <span>Card art: Vector Playing Cards (public domain)</span>
</footer>
</main>

<script>{JS}</script>
</body>
</html>
'''

open('/tmp/poker-hands/poker-hands.html', 'w').write(page)
print('wrote', len(page), 'bytes')
