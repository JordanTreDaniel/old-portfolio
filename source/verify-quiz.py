#!/usr/bin/env python3
"""Independent re-check of v2-quiz-content.json: reload from disk, fresh evaluator."""
import json, itertools, re, sys

D = json.load(open('/tmp/poker-hands/v2-quiz-content.json'))
SRC = json.load(open('/tmp/poker-hands/hands-content.json'))
RV = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
      '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
NM = {0: 'high card', 1: 'one pair', 2: 'two pair', 3: 'three of a kind',
      4: 'straight', 5: 'flush', 6: 'full house', 7: 'four of a kind',
      8: 'straight flush'}
ok = True


def ev(cs):
    v = sorted((RV[c[:-1]] for c in cs), reverse=True)
    s = [c[-1] for c in cs]
    fl = len(set(s)) == 1
    u = sorted(set(v), reverse=True)
    st = None
    if len(u) == 5:
        if u[0] - u[4] == 4:
            st = u[0]
        elif u == [14, 5, 4, 3, 2]:
            st = 5
    cnt = {x: v.count(x) for x in set(v)}
    g = sorted(cnt, key=lambda x: (cnt[x], x), reverse=True)
    if fl and st:
        return 8, (st,)
    if cnt[g[0]] == 4:
        return 7, (g[0], [x for x in g if x != g[0]][0])
    if cnt[g[0]] == 3 and cnt[g[1]] == 2:
        return 6, (g[0], g[1])
    if fl:
        return 5, tuple(v)
    if st:
        return 4, (st,)
    if cnt[g[0]] == 3:
        return 3, (g[0], *sorted((x for x in v if x != g[0]), reverse=True))
    if cnt[g[0]] == 2 and cnt[g[1]] == 2:
        hp, lp = g[0], g[1]
        return 2, (hp, lp, max(x for x in v if x not in (hp, lp)))
    if cnt[g[0]] == 2:
        return 1, (g[0], *sorted((x for x in v if x != g[0]), reverse=True))
    return 0, tuple(v)


def best(seven):
    vals = [(ev(list(c)), c) for c in itertools.combinations(seven, 5)]
    m = max(v for v, _ in vals)
    return m, [c for v, c in vals if v == m]


# schema
assert set(D) == {'quiz', 'traps', 'seo'}, set(D)
assert len(D['quiz']) == 5 and len(D['traps']) == 7
internal = {'bait_tap', 'bait_checks', '_src_index'}

qkeys = {'id', 'title', 'hole', 'board', 'best5', 'hand_name', 'distractor_note', 'prompt'}
tkeys = {'id', 'mistake_ref', 'bait_title', 'hole', 'board', 'correct_best5',
         'wrong_answer_cards', 'correct_hand_name', 'trap_rule', 'why_the_bait_fails'}

print('QUIZ:')
for i, q in enumerate(D['quiz']):
    assert not (set(q) - qkeys), (q['id'], set(q) - qkeys)
    src = SRC['interaction']['examples'][i]
    copied = (q['hole'], q['board'], q['best5'])
    exp = ([c[:-1] + {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}[c[-1]] for c in src['hole']],
           [c[:-1] + {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}[c[-1]] for c in src['board']],
           [c[:-1] + {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}[c[-1]] for c in src['best5']])
    m = copied == exp
    opt, wins = best(q['hole'] + q['board'])
    val = ev(q['best5'])
    p = m and val == opt and NM[opt[0]] == q['hand_name'].lower() \
        and q['prompt'] == ('Tap the 5 cards that make your best hand — the hand name stays hidden '
                            'until you nail all five')
    ok &= p
    print(f"  {'PASS' if p else 'FAIL'}  {q['id']}  copied_from_source={m} "
          f"optimal={val == opt} hand={NM[opt[0]]}")

# bait taps are not in the output file (internal), so re-derive illegitimacy facts
print('TRAPS:')
bait_meta = {  # id -> (illegitimacy assertion on the 7 cards / claimed reading)
    'trap-must-use-both-hole-cards': lambda s, b5: ev(s)[0] != 0 and ev(b5)[0] == 5,
    'trap-six-or-seven-cards': lambda s, b5: len(s) > 5,
    'trap-board-cannot-play-itself': lambda s, b5: ev(['9D', '8H', '7C', '6S', '5D'])[0] == 4,
    'trap-suited-is-not-a-flush': lambda s, b5: sum(c[-1] == 'S' for c in s) == 4,
    'trap-ace-kicker-is-not-a-hand': lambda s, b5: 'AS' not in b5 and ev(b5)[0] == 6,
    'trap-ace-cannot-wrap': lambda s, b5: ev(['QC', 'KS', 'AS', '2H', '3C'])[0] != 4
                                          and ev(b5) == (4, (5,)),
    'trap-connectors-are-not-a-straight-flush':
        lambda s, b5: all(ev(list(c))[0] != 8 for c in itertools.combinations(s, 5))
                      and sum(c[-1] == 'S' for c in s) < 5,
}
for j, t in enumerate(D['traps']):
    assert not (set(t) - tkeys), (t['id'], set(t) - tkeys)
    seven = t['hole'] + t['board']
    p1 = t['mistake_ref'] == j and 0 <= j < 7
    p2 = len(seven) == 7 == len(set(seven)) and all(re.fullmatch(r'(10|[2-9]|J|Q|K|A)[SHDC]', c) for c in seven)
    opt, wins = best(seven)
    p3 = ev(t['correct_best5']) == opt and len(set(t['correct_best5'])) == 5
    p4 = NM[opt[0]] == t['correct_hand_name'].lower()
    p5 = 1 <= len(t['wrong_answer_cards']) <= 3 \
        and set(t['wrong_answer_cards']) <= set(seven) \
        and not (set(t['wrong_answer_cards']) & set(t['correct_best5']))
    p6 = bait_meta[t['id']](seven, t['correct_best5'])
    p = p1 and p2 and p3 and p4 and p5 and p6
    ok &= p
    print(f"  {'PASS' if p else 'FAIL'}  {t['id']} ref={t['mistake_ref']} "
          f"optimal={p3} name={p4} wrong_cards={p5} bait_illegit={p6} hand={NM[opt[0]]}")

s = D['seo']
p = (140 <= len(s['meta_description']) <= 165 and 'poker hands for beginners'
     in s['meta_description'].lower() and 45 <= len(s['title_tag']) <= 65
     and s['json_ld']['@type'] == 'FAQPage' and len(s['json_ld']['mainEntity']) == 9)
ok &= p
print(f"SEO: {'PASS' if p else 'FAIL'}  meta={len(s['meta_description'])} chars, "
      f"title={len(s['title_tag'])} chars, faq={len(s['json_ld']['mainEntity'])} Q&As")
print('ALL CHECKS PASS' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
