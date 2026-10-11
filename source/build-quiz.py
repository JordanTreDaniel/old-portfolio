#!/usr/bin/env python3
"""Build + machine-verify /tmp/poker-hands/v2-quiz-content.json.

Section 1 'quiz'  : 5 entries derived from interaction.examples[] (cards copied).
Section 2 'traps' : 7 entries, one per interaction.mistakes[] entry, each with a
                    NEW baited example. Exhaustive C(7,5) verification of every
                    correct_best5, plus per-trap bait-legitimacy checks.
Top-level 'seo'   : meta_description, title_tag, json_ld (FAQPage).

Card notation in arrays: ASCII <RANK><SUIT> (QS, 10D, AH) per task spec.
Prose uses unicode suits (matches hands-content.json style).
"""
import json, itertools, re, sys

SRC = json.load(open('/tmp/poker-hands/hands-content.json'))

SUITS = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
SUIT_SYM = {v: k for k, v in SUITS.items()}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VAL = {r: i + 2 for i, r in enumerate(RANKS)}  # 2..14
CATEGORY_NAME = {
    0: 'high card', 1: 'one pair', 2: 'two pair', 3: 'three of a kind',
    4: 'straight', 5: 'flush', 6: 'full house', 7: 'four of a kind',
    8: 'straight flush',
}


def to_code(card: str) -> str:
    """'10♠' -> '10S'."""
    return card[:-1] + SUITS[card[-1]]


def parse(card: str):
    m = re.fullmatch(r'(10|[2-9]|J|Q|K|A)([SHDC])', card)
    assert m, f'bad card notation: {card!r}'
    return RANK_VAL[m.group(1)], m.group(2)


def eval5(cards):
    """Return (category, tiebreak_tuple) for a 5-card hand. A can be low in a straight."""
    assert len(cards) == 5 and len(set(cards)) == 5, cards
    vals = sorted((parse(c)[0] for c in cards), reverse=True)
    suits = [parse(c)[1] for c in cards]
    is_flush = len(set(suits)) == 1
    uniq = sorted(set(vals), reverse=True)
    straight_high = None
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        elif uniq == [14, 5, 4, 3, 2]:
            straight_high = 5          # wheel A-2-3-4-5
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    if is_flush and straight_high:
        return 8, (straight_high,)
    if groups[0][1] == 4:
        return 7, (groups[0][0], groups[1][0])
    if groups[0][1] == 3 and groups[1][1] == 2:
        return 6, (groups[0][0], groups[1][0])
    if is_flush:
        return 5, tuple(vals)
    if straight_high:
        return 4, (straight_high,)
    if groups[0][1] == 3:
        kickers = sorted((v for v in vals if v != groups[0][0]), reverse=True)
        return 3, (groups[0][0], *kickers)
    if groups[0][1] == 2 and groups[1][1] == 2:
        hp, lp = groups[0][0], groups[1][0]
        kicker = max(v for v in vals if v not in (hp, lp))
        return 2, (hp, lp, kicker)
    if groups[0][1] == 2:
        kickers = sorted((v for v in vals if v != groups[0][0]), reverse=True)
        return 1, (groups[0][0], *kickers)
    return 0, tuple(vals)


def best_of_7(seven):
    """Exhaustive C(7,5): returns (value, [all optimal 5-card selections])."""
    best, winners = None, []
    for combo in itertools.combinations(seven, 5):
        v = eval5(list(combo))
        if best is None or v > best:
            best, winners = v, [combo]
        elif v == best:
            winners.append(combo)
    return best, winners


# ------------------------------------------------------------------ SECTION 1
# Titles / distractors authored per example; hole/board/best5 COPIED from source.
QUIZ_META = [
    dict(
        id='quiz-both-hole-cards',
        title='What hand do you actually have?',
        hand_name='Straight',
        distractor_note=(
            "The board waves a big K and Q at you, but they connect with nothing, and "
            "4-3-2 on its own is only three cards in a row. Beginners either tap the two "
            "highest cards for 'high card' or miss that your 5 and 6 slot exactly on top of "
            "the board's 4-3-2. Drop either hole card and the straight disappears.")),
    dict(
        id='quiz-one-hole-card-trips',
        title='Which five cards are your hand?',
        hand_name='Three of a kind',
        distractor_note=(
            "Two queens already sit on the board, so it's easy to either stop at 'two pair "
            "on the board' and miss that your Q♠ makes trips — or to force your 2♦ in as a "
            "kicker when the board's J♣ and 9♠ are better cards. Only one hole card counts here.")),
    dict(
        id='quiz-playing-the-board',
        title='Can the board win all by itself?',
        hand_name='Flush',
        distractor_note=(
            "Your hole cards are right there and feel impossible to throw away, so beginners "
            "dig in and try to use at least one of them. But all five community cards are hearts, "
            "and nothing 3♣ 4♠ can build beats a five-card flush — your best hand literally IS the board.")),
    dict(
        id='quiz-kickers-a',
        title='Which five cards win it?',
        hand_name='One pair',
        distractor_note=(
            "Everyone pairs the board's kings and both players hold an ace, so K-K-A is a tie. "
            "Beginners stop comparing there and never get to the fourth card — your 9♦ over the "
            "opponent's 8 is the entire pot.")),
    dict(
        id='quiz-kickers-b',
        title='Which five cards win it?',
        hand_name='One pair',
        distractor_note=(
            "With an ace in hand it feels like a winner, but after K-K-A on both sides the "
            "comparison rolls to the fourth card: your 8♥ — and that's exactly where Player A "
            "pulls ahead with a 9. Your 7♣ as the fifth card never even gets compared.")),
]

QUIZ_PROMPT = 'Tap the 5 cards that make your best hand — then name the hand'

quiz = []
for i, (src, meta) in enumerate(zip(SRC['interaction']['examples'], QUIZ_META)):
    quiz.append({
        'id': meta['id'],
        'title': meta['title'],
        'hole': [to_code(c) for c in src['hole']],
        'board': [to_code(c) for c in src['board']],
        'best5': [to_code(c) for c in src['best5']],
        'hand_name': meta['hand_name'],
        'distractor_note': meta['distractor_note'],
        'prompt': QUIZ_PROMPT,
        '_src_index': i,   # index into interaction.examples[] (for verification)
    })

# ------------------------------------------------------------------ SECTION 2
traps = [
    dict(
        id='trap-must-use-both-hole-cards',
        mistake_ref=0,
        bait_title='You paired your jack — one pair!',
        hole=['JS', '4C'],
        board=['JH', 'QH', '10H', '8H', '2H'],
        correct_best5=['QH', 'JH', '10H', '8H', '2H'],
        wrong_answer_cards=['JS', '4C'],
        correct_hand_name='Flush',
        trap_rule=("You never have to use both of your hole cards: your hand is the best 5 cards "
                   "out of your 7. If the board already beats what your cards make, throw your "
                   "hole cards away."),
        why_the_bait_fails=(
            "By insisting both hole cards count, you build J-J-Q-10-4 — a mere pair of jacks. "
            "But the five hearts on the board (Q♥ J♥ 10♥ 8♥ 2♥) are already a flush, and a flush "
            "beats a pair. Tapping JS and 4C actually forces you to drop two hearts; your true "
            "best 5 is all five board cards."),
        bait_tap=['JS', '4C', 'JH', 'QH', '10H'],
        bait_checks=['board_flush_beats_bait', 'bait_uses_both_hole_cards'],
    ),
    dict(
        id='trap-six-or-seven-cards',
        mistake_ref=1,
        bait_title='A straight AND a pair of kings — that\'s seven cards!',
        hole=['8S', '7S'],
        board=['6H', '5D', '4C', 'KS', 'KD'],
        correct_best5=['8S', '7S', '6H', '5D', '4C'],
        wrong_answer_cards=['KS', 'KD'],
        correct_hand_name='Straight',
        trap_rule=("A poker hand is always exactly 5 cards — you can never count 6 or 7. "
                   "Pick your strongest 5 and stop."),
        why_the_bait_fails=(
            "You can't stack the board's pair of kings on top of your straight — that would be a "
            "7-card 'hand'. Your best 5 is 8-7-6-5-4 (8♠ 7♠ 6♥ 5♦ 4♣) and a straight beats a pair. "
            "If you tap the kings to 'keep both', you've downgraded yourself to a single pair "
            "(K-K-8-7-6) and thrown the straight away."),
        bait_tap=['KS', 'KD', '8S', '7S', '6H'],
        bait_checks=['claimed_set_gt_5_cards', 'bait_is_worse_category'],
    ),
    dict(
        id='trap-board-cannot-play-itself',
        mistake_ref=2,
        bait_title='Ace-king high — the big cards win it!',
        hole=['AS', 'KC'],
        board=['9D', '8H', '7C', '6S', '5D'],
        correct_best5=['9D', '8H', '7C', '6S', '5D'],
        wrong_answer_cards=['AS', 'KC'],
        correct_hand_name='Straight',
        trap_rule=("The board CAN make a hand all by itself — five community cards can form a "
                   "straight, flush, full house or even four of a kind, and 'playing the board' is legal."),
        why_the_bait_fails=(
            "Your ace and king connect with nothing (no Q-J-10 to complete a Broadway run), so "
            "A-K-9-8-7 is only high card. The five board cards already run 9-8-7-6-5 — a straight — "
            "and a straight beats any high card. Your best 5 IS the board; both hole cards are discarded."),
        bait_tap=['AS', 'KC', '9D', '8H', '7C'],
        bait_checks=['board_alone_straight', 'bait_uses_both_hole_cards'],
    ),
    dict(
        id='trap-suited-is-not-a-flush',
        mistake_ref=3,
        bait_title='Four spades — you made a flush!',
        hole=['AS', '9S'],
        board=['KS', '8H', '7D', '6C', '5S'],
        correct_best5=['9S', '8H', '7D', '6C', '5S'],
        wrong_answer_cards=['AS', 'KS'],
        correct_hand_name='Straight',
        trap_rule=("Suited hole cards are only a head start — a flush needs FIVE cards of the same "
                   "suit, and among your seven cards you only have four spades."),
        why_the_bait_fails=(
            "Count the spades: A♠ 9♠ K♠ 5♠ — four of them, and four cards can't make a five-card "
            "flush (your fifth tap would be a non-spade). You've also thrown away your real hand: "
            "9♠ 8♥ 7♦ 6♣ 5♠ is a straight, which beats the ace-high you'd be left with."),
        bait_tap=['AS', '9S', 'KS', '5S', '8H'],
        bait_checks=['only_four_of_suit', 'bait_not_flush'],
    ),
    dict(
        id='trap-ace-kicker-is-not-a-hand',
        mistake_ref=4,
        bait_title='Your ace kicker wins the showdown!',
        hole=['AS', '4D'],
        board=['KH', 'KC', 'KD', 'QS', 'QC'],
        correct_best5=['KH', 'KC', 'KD', 'QS', 'QC'],
        wrong_answer_cards=['AS'],
        correct_hand_name='Full house',
        trap_rule=("Kickers only compare when both hands are the SAME type — an ace is a tiebreaker, "
                   "never a hand on its own."),
        why_the_bait_fails=(
            "Tapping A♠ gives you three kings with an ace kicker — but you've ignored the full house "
            "sitting on the board (K♥ K♣ K♦ Q♠ Q♣), a higher hand category that needs zero hole cards. "
            "Your ace isn't even in your best 5 here, so it can't win anything, and kicker comparisons "
            "only ever happen between two hands of the same rank."),
        bait_tap=['AS', 'KH', 'KC', 'KD', 'QS'],
        bait_checks=['ace_not_in_best5', 'bait_is_worse_category'],
    ),
    dict(
        id='trap-ace-cannot-wrap',
        mistake_ref=5,
        bait_title='Q-K-A-2-3 — that\'s a straight, right?',
        hole=['AS', '4D'],
        board=['2H', '3C', '5D', 'KS', 'QC'],
        correct_best5=['AS', '5D', '4D', '3C', '2H'],
        wrong_answer_cards=['QC', 'KS'],
        correct_hand_name='Straight',
        trap_rule=("For straights only, an ace can be the LOW card — A-2-3-4-5 is a real straight — "
                   "but it can never wrap around: Q-K-A-2-3 is not a straight."),
        why_the_bait_fails=(
            "A run steps in one direction: the ace counts as high (above K) or low (below 2), never "
            "both, so K-A-2 can't continue around the corner. Tapping Q♣ K♠ A♠ 2♥ 3♣ leaves you with "
            "nothing but ace-high. Meanwhile your actual best 5 is the straight you overlooked — the "
            "wheel: A♠ 2♥ 3♣ 4♦ 5♦."),
        bait_tap=['QC', 'KS', 'AS', '2H', '3C'],
        bait_checks=['bait_is_not_straight', 'correct_is_wheel'],
    ),
    dict(
        id='trap-connectors-are-not-a-straight-flush',
        mistake_ref=6,
        bait_title='Straight flush — your 9♠ 8♠ came in!',
        hole=['9S', '8S'],
        board=['7S', '6H', '5D', 'JS', '10D'],
        correct_best5=['JS', '10D', '9S', '8S', '7S'],
        wrong_answer_cards=['6H', '5D'],
        correct_hand_name='Straight',
        trap_rule=("A straight flush needs five cards in a row AND all the same suit — suited "
                   "connectors are only a starting point, never a made hand."),
        why_the_bait_fails=(
            "The run you're seeing (9-8-7-6-5) isn't all spades: only 4 of your 7 cards are spades, "
            "and the 6 and 5 on the board are 6♥ and 5♦ — so there's no flush, let alone a straight "
            "flush. Tapping that run also leaves your best hand on the table: J♠ 10♦ 9♠ 8♠ 7♠ is a "
            "J-high straight, and it beats the 9-high run you tapped."),
        bait_tap=['9S', '8S', '7S', '6H', '5D'],
        bait_checks=['no_straight_flush_exists', 'bait_is_lower_straight'],
    ),
]

# ------------------------------------------------------------------ SECTION 3
META_DESC = ("Poker hands for beginners: 10 rankings from royal flush to high card, how "
             "best-5-of-7 works, kickers explained, and 7 classic beginner mistakes to teach.")
TITLE_TAG = 'Poker Hands for Beginners: Rankings, Quiz & Mistakes'

JSON_LD = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    'mainEntity': [
        {'@type': 'Question', 'name': 'What is the best hand in poker?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'A royal flush — the 10, jack, queen, king and ace all of the same suit. It is the '
             'highest straight flush, so it beats every other poker hand; you are dealt one about '
             '1 in 649,740 times, and it can never lose.'}},
        {'@type': 'Question', 'name': 'What is the worst hand in poker?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'High card. With no pair, straight or flush you play your single highest card, and it '
             'only wins if everyone else also has nothing — even then, only if your top card is the biggest.'}},
        {'@type': 'Question', 'name': 'What is the correct order of poker hands?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'From strongest to weakest: royal flush, straight flush, four of a kind, full house, '
             'flush, straight, three of a kind, two pair, one pair, high card.'}},
        {'@type': 'Question', 'name': 'How many cards are in a poker hand?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'Exactly five. In Texas Hold\u2019em you pick the best 5 cards from your 2 hole cards '
             'plus the 5 community cards — the \u201cbest 5 of 7\u201d — and you never show 6 or 7 cards.'}},
        {'@type': 'Question', 'name': 'Do you have to use both of your hole cards?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'No. You may use both, just one, or neither — your hand is simply the best 5-card '
             'combination of your seven cards. If the five community cards already beat anything '
             'your cards make, you play the board.'}},
        {'@type': 'Question', 'name': 'What is a kicker in poker?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'A kicker is a leftover high card used to break ties. When two players make the same '
             'kind of hand — say, both pair the board\u2019s kings — the next-highest cards are '
             'compared one at a time until one player pulls ahead; identical kickers split the pot.'}},
        {'@type': 'Question', 'name': 'What is the difference between a flush and a straight?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'A flush is five cards that all share one suit but are not in order (like 9\u2665 8\u2665 '
             '5\u2665 2\u2665 K\u2665); a straight is five cards in consecutive rank order from mixed '
             'suits (like 9\u2663 8\u2666 7\u2665 6\u2660 5\u2663). A flush beats a straight.'}},
        {'@type': 'Question', 'name': 'Is A-2-3-4-5 a straight in poker?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
             'Yes. For straights only, an ace can count as the low card, so A-2-3-4-5 is a straight '
             '— the lowest one. But the ace can never wrap around the end: Q-K-A-2-3 is not a straight.'}},
    ],
}

seo = {'meta_description': META_DESC, 'title_tag': TITLE_TAG, 'json_ld': JSON_LD}

# ------------------------------------------------------------------ VERIFY
results, failures = [], []


def fail(ex_id, msg):
    failures.append(f'{ex_id}: {msg}')
    results.append({'id': ex_id, 'status': 'FAIL', 'detail': msg})


def verify_example(ex_id, hole, board, best5, extra=None):
    seven = hole + board
    problems = []
    if len(seven) != 7 or len(set(seven)) != 7:
        problems.append('hole+board is not 7 distinct cards')
    for c in seven:
        parse(c)
    if len(best5) != 5 or len(set(best5)) != 5:
        problems.append('best5 is not exactly 5 distinct cards')
    if not set(best5) <= set(seven):
        problems.append('best5 contains cards not in hole+board')
    given = eval5(best5) if len(best5) == 5 else None
    opt, winners = best_of_7(seven)
    if given != opt:
        problems.append(f'best5 {given} is not optimal {opt} (winners: {winners})')
    for name, fn in (extra or {}).items():
        try:
            ok, detail = fn(seven, best5, opt)
        except Exception as e:  # noqa: BLE001
            ok, detail = False, repr(e)
        if not ok:
            problems.append(f'{name}: {detail}')
    if problems:
        fail(ex_id, '; '.join(problems))
        return None
    res = {'id': ex_id, 'status': 'PASS',
           'hand': CATEGORY_NAME[opt[0]],
           'optimal_tiebreak': list(opt[1]),
           'n_optimal_selections': len(winners)}
    results.append(res)
    return opt


# --- quiz verification -------------------------------------------------------
for q in quiz:
    src = SRC['interaction']['examples'][q['_src_index']]
    ex_id = q['id']
    if q['hole'] != [to_code(c) for c in src['hole']] or \
       q['board'] != [to_code(c) for c in src['board']] or \
       q['best5'] != [to_code(c) for c in src['best5']]:
        fail(ex_id, 'cards do not exactly match the source example')
        continue
    extra = {
        'hand_name_matches': lambda seven, b5, opt, q=q:
            (CATEGORY_NAME[opt[0]] == q['hand_name'].lower(),
             f"declared {q['hand_name']!r} vs actual {CATEGORY_NAME[opt[0]]!r}"),
    }
    verify_example(ex_id, q['hole'], q['board'], q['best5'], extra)

# --- trap verification -------------------------------------------------------
mistakes = SRC['interaction']['mistakes']


def bait_strictly_worse(bait_val_fn):
    return None  # placeholder; handled inline below


for t in traps:
    ex_id = t['id']
    seven = t['hole'] + t['board']
    problems = []
    # schema sanity
    if not (0 <= t['mistake_ref'] < len(mistakes)):
        problems.append(f"mistake_ref {t['mistake_ref']} out of range")
    if not (1 <= len(t['wrong_answer_cards']) <= 3):
        problems.append('wrong_answer_cards must have 1-3 cards')
    if not set(t['wrong_answer_cards']) <= set(seven):
        problems.append('wrong_answer_cards not a subset of hole+board')
    if set(t['wrong_answer_cards']) & set(t['correct_best5']):
        problems.append('wrong_answer_cards overlaps correct_best5')
    # bait tap must be a legal 5-card selection from the 7 and strictly worse
    bt = t['bait_tap']
    if len(bt) != 5 or len(set(bt)) != 5 or not set(bt) <= set(seven):
        problems.append(f'bait_tap {bt} is not 5 distinct cards from the 7')
    else:
        bv, ov = eval5(bt), eval5(t['correct_best5'])
        if bv >= ov:
            problems.append(f'bait_tap value {bv} not strictly worse than correct {ov}')
    # per-trap illegitimacy checks
    checks = {
        'board_flush_beats_bait': lambda s, b5: (
            eval5(b5)[0] == 5, 'correct best5 should be a flush'),
        'bait_uses_both_hole_cards': lambda s, b5: (
            set(t['hole']) <= set(t['bait_tap']), 'bait tap should include both hole cards'),
        'claimed_set_gt_5_cards': lambda s, b5: (
            len(set(t['hole'] + t['board'])) > 5, 'bait claims >5 cards'),
        'bait_is_worse_category': lambda s, b5: (
            eval5(t['bait_tap'])[0] < eval5(b5)[0], 'bait should be a strictly lower category'),
        'board_alone_straight': lambda s, b5: (
            eval5(t['board'])[0] == 4, 'board alone should already be a straight'),
        'only_four_of_suit': lambda s, b5: (
            sum(1 for c in s if parse(c)[1] == parse(t['hole'][0])[1]) == 4,
            'exactly 4 of the hole suit should exist among the 7'),
        'bait_not_flush': lambda s, b5: (
            eval5(t['bait_tap'])[0] != 5, 'bait tap must not be a flush'),
        'ace_not_in_best5': lambda s, b5: (
            'AS' not in b5, 'the ace should be absent from the optimal best5'),
        'bait_is_not_straight': lambda s, b5: (
            eval5(t['bait_tap'])[0] != 4, 'wrap tap must NOT score as a straight'),
        'correct_is_wheel': lambda s, b5: (
            eval5(b5) == (4, (5,)) and 'AS' in b5, 'correct best5 should be the A-2-3-4-5 wheel'),
        'no_straight_flush_exists': lambda s, b5: (
            all(eval5(list(c))[0] != 8 for c in itertools.combinations(s, 5)),
            'a straight flush must not exist anywhere in the 7'),
        'bait_is_lower_straight': lambda s, b5: (
            eval5(t['bait_tap'])[0] == 4 and eval5(b5)[0] == 4
            and eval5(t['bait_tap'])[1][0] < eval5(b5)[1][0],
            'bait should be a straight but lower than correct'),
    }
    for name in t['bait_checks']:
        fn = checks[name]
        seven_chk, b5_chk = seven, t['correct_best5']
        ok, detail = fn(seven_chk, b5_chk)
        if not ok:
            problems.append(f'{name}: {detail}')
    if problems:
        fail(ex_id, '; '.join(problems))
        continue
    opt = verify_example(ex_id, t['hole'], t['board'], t['correct_best5'])
    if opt and CATEGORY_NAME[opt[0]] != t['correct_hand_name'].lower():
        fail(ex_id, f"correct_hand_name {t['correct_hand_name']!r} != actual {CATEGORY_NAME[opt[0]]!r}")

# --- content sanity ----------------------------------------------------------
if len(SRC['interaction']['mistakes']) != 7:
    fail('mistakes', 'source mistakes[] is not length 7')
if sorted(t['mistake_ref'] for t in traps) != list(range(7)):
    fail('traps', 'mistake_ref must cover 0..6 exactly once')
if not (140 <= len(META_DESC) <= 165):
    fail('seo', f'meta_description length {len(META_DESC)} outside 140-165')
if not (45 <= len(TITLE_TAG) <= 65):
    fail('seo', f'title_tag length {len(TITLE_TAG)} outside 45-65')
if 'poker hands for beginners' not in META_DESC.lower():
    fail('seo', 'meta_description missing exact keyword phrase')
if JSON_LD.get('@type') != 'FAQPage' or len(JSON_LD['mainEntity']) < 5:
    fail('seo', 'json_ld must be an FAQPage with >=5 Q&As')

# --- write -------------------------------------------------------------------
# capture bait evaluations before internal fields are stripped
bait_report = []
for t in traps:
    bv = eval5(t['bait_tap'])
    ov = eval5(t['correct_best5'])
    bait_report.append({
        'id': t['id'],
        'bait_tap': t['bait_tap'],
        'bait_claim': t['bait_title'],
        'bait_tap_actually_is': CATEGORY_NAME[bv[0]],
        'correct_best5_actually_is': CATEGORY_NAME[ov[0]],
        'strictly_worse': bv < ov,
    })

out = {'quiz': [{k: v for k, v in q.items() if k != '_src_index'} for q in quiz],
       'traps': traps, 'seo': seo}
# drop internal verification fields from traps
for t in out['traps']:
    t.pop('bait_tap', None)
    t.pop('bait_checks', None)
with open('/tmp/poker-hands/v2-quiz-content.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')

# --- report ------------------------------------------------------------------
print(f'meta_description: {len(META_DESC)} chars | title_tag: {len(TITLE_TAG)} chars')
print(f'quiz entries: {len(out["quiz"])} | trap entries: {len(out["traps"])} | '
      f'faq Q&As: {len(JSON_LD["mainEntity"])}')
print()
for r in results:
    extra = ''
    if 'hand' in r:
        extra = f" hand={r['hand']} tiebreak={r['optimal_tiebreak']} optimal_selections={r['n_optimal_selections']}"
    print(f"{r['status']:4}  {r['id']}{extra}"
          + (f"  -- {r['detail']}" if r['status'] == 'FAIL' else ''))
print()
# bait tap evaluations for the pedagogy review
print("Bait evaluations (fool's 5-card tap -> what it really is vs what's correct):")
for b in bait_report:
    print(f"  {b['id']}: claim={b['bait_claim']!r}")
    print(f"      tap {b['bait_tap']} -> actually {b['bait_tap_actually_is']!r}; "
          f"correct = {b['correct_best5_actually_is']!r}; strictly_worse={b['strictly_worse']}")
print(f'total checks: {len(results)} | failures: {len(failures)}')
for fmsg in failures:
    print('  FAIL:', fmsg)
sys.exit(1 if failures else 0)
