import gc
import json
import sys
import time

try:
    import py_fallback
except Exception as _imp_err:
    sys.stderr.write(f"WARN: py_fallback import failed ({_imp_err}); using built-in heuristic fallback.\n")
    sys.stderr.flush()
    py_fallback = None

SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {
    '2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
    '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12
}
STREET_MAP = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}


def _pair_strength(c1, c2):
    r1, s1 = RANK_MAP[c1[0]], SUIT_MAP[c1[1]]
    r2, s2 = RANK_MAP[c2[0]], SUIT_MAP[c2[1]]
    hi, lo = max(r1, r2), min(r1, r2)
    score = hi * 20 + lo * 10
    if r1 == r2:
        score += 200 + r1 * 15
    if s1 == s2:
        score += 28
    if hi - lo == 1:
        score += 18
    elif hi - lo == 2:
        score += 10
    return score


def _compute_dynamic_budget_ms(time_left_ms, hands_played, total_hands, pot, street, is_discard=False):
    hands_rem = max(1, total_hands - hands_played)
    usable_ms = max(400.0, time_left_ms * 0.70)
    per_hand_ms = usable_ms / hands_rem
    base = per_hand_ms * (0.20 if is_discard else 0.32)
    if pot >= 60:
        base *= 1.45
    elif pot >= 24:
        base *= 1.20
    if street in ("turn", "river"):
        base *= 1.15
    lo, hi = (1.8, 5.5) if is_discard else (2.2, 8.5)
    return max(lo, min(hi, base))


class OpponentTracker:
    def __init__(self):
        self.hands = 0
        self.vpip_hands = 0
        self.opp_actions = 0.0
        self.opp_raises = 0.0
        self.faced_bets_pre = 0.0
        self.folded_to_bets_pre = 0.0
        self.faced_bets_post = 0.0
        self.folded_to_bets_post = 0.0
        self.sd_count = 0
        self.sd_weak_sum = 0.0
        self.net_chips = 0

    def update_from_result(self, msg):
        history = msg.get("history", [])
        if history:
            self.hands += 1
            opp_put_money = False
            my_last_bet_street = None
            opp_first_preflop_acted = False
            for entry in history:
                if isinstance(entry, dict):
                    actor = entry.get("player", entry.get("actor", ""))
                    act = entry.get("action", "")
                    street = entry.get("street")
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    actor, act = entry[0], entry[1]
                    street = entry[2] if len(entry) >= 3 else None
                else:
                    continue

                is_opp = (actor in ("opp", 1, "B"))
                if is_opp:
                    self.opp_actions += 1.0
                    is_pre = (street in (None, "preflop") and not opp_first_preflop_acted) or (street == "preflop")
                    if is_pre:
                        if act in ("call", "raise", "bet"):
                            opp_put_money = True
                        if not opp_first_preflop_acted:
                            opp_first_preflop_acted = True
                            if my_last_bet_street is None:
                                self.faced_bets_pre += 1.0
                                if act == "fold":
                                    self.folded_to_bets_pre += 1.0
                    if act in ("raise", "bet"):
                        self.opp_raises += 1.0
                    if my_last_bet_street is not None:
                        if my_last_bet_street == "preflop":
                            self.faced_bets_pre += 1.0
                            if act == "fold":
                                self.folded_to_bets_pre += 1.0
                        else:
                            self.faced_bets_post += 1.0
                            if act == "fold":
                                self.folded_to_bets_post += 1.0
                    my_last_bet_street = None
                else:
                    if act in ("raise", "bet"):
                        my_last_bet_street = street if street is not None else "postflop"
                    elif act in ("call", "check", "fold"):
                        my_last_bet_street = None

            if opp_put_money:
                self.vpip_hands += 1

        delta = msg.get("net", msg.get("delta", msg.get("my_delta", msg.get("payoff", 0))))
        if isinstance(delta, (int, float)):
            self.net_chips += int(delta)

        opp_cards = msg.get("opp_hole_cards")
        if isinstance(opp_cards, list) and len(opp_cards) >= 2:
            strength = _pair_strength(opp_cards[0], opp_cards[1])
            looseness = max(-1.0, min(1.0, (235.0 - strength) / 120.0))
            self.sd_count += 1
            self.sd_weak_sum += looseness

    def get_stats(self):
        vpip = (self.vpip_hands + 4.0) / (self.hands + 8.0)
        agg = (self.opp_raises + 3.0) / (self.opp_actions + 12.0)
        fold_pre = (self.folded_to_bets_pre + 2.0) / (self.faced_bets_pre + 6.0)
        fold_post = (self.folded_to_bets_post + 3.0) / (self.faced_bets_post + 8.0)
        sd_loose = self.sd_weak_sum / (self.sd_count + 4.0)
        return (
            max(0.10, min(0.95, vpip)),
            max(0.05, min(0.85, agg)),
            max(0.10, min(0.90, fold_pre)),
            max(0.10, min(0.90, fold_post)),
            max(-1.0, min(1.0, sd_loose)),
        )


class LiveState:
    __slots__ = ['hole', 'flop_board_ids', 'dead', 'opp_discard_id', 'is_button', 'opp_raised']

    def __init__(self):
        self.hole = []
        self.flop_board_ids = []
        self.dead = 0
        self.opp_discard_id = -1
        self.is_button = 0
        self.opp_raised = 0


def parse_card_id(card_str):
    return SUIT_MAP[card_str[1]] * 13 + RANK_MAP[card_str[0]]


def legalize_action(req, action_type, amount=0):
    legal = req.get("legal_actions", [])
    if action_type == "raise" and "raise" in legal:
        min_r = int(req.get("min_raise", 0))
        max_r = int(req.get("max_raise", 0))
        if min_r <= max_r and max_r > 0:
            clamped = max(min_r, min(max_r, int(amount)))
            return {"type": "action", "action": "raise", "amount": clamped}
        action_type = "call" if "call" in legal else "check"

    if action_type in legal:
        return {"type": "action", "action": action_type}

    if "check" in legal:
        return {"type": "action", "action": "check"}
    if "call" in legal:
        return {"type": "action", "action": "call"}
    if "fold" in legal:
        return {"type": "action", "action": "fold"}
    if legal:
        if legal[0] == "raise":
            return {"type": "action", "action": "raise", "amount": int(req.get("min_raise", 0))}
        return {"type": "action", "action": legal[0]}
    return {"type": "action", "action": "check"}


def _fast_heuristic_discard(cards, board_cards):
    # O(1) deterministic fallback: keep pair/board-hit/flush-draw/high-card
    branks = {c[0] for c in board_cards}
    bsuits = [c[1] for c in board_cards]
    best_drop, best_sc = 0, -999
    for d in range(len(cards)):
        kept = [cards[i] for i in range(len(cards)) if i != d]
        if len(kept) < 2:
            continue
        sc = _pair_strength(kept[0], kept[1])
        for kc in kept:
            if kc[0] in branks:
                sc += 180 + RANK_MAP.get(kc[0], 0) * 10
            if bsuits.count(kc[1]) >= 2:
                sc += 35
        if sc > best_sc:
            best_sc, best_drop = sc, d
    return cards[best_drop]


def _fast_heuristic_action(req, hole):
    # O(1) deterministic fallback when time_left_ms < 300ms
    legal = req.get("legal_actions", [])
    board = req.get("board", [])
    pot = max(2, int(req.get("pot", 2)))
    to_call = int(req.get("to_call", 0))
    branks = {c[0] for c in board}
    ranks = [RANK_MAP.get(c[0], 0) for c in hole]
    has_pair = (len(set(ranks)) < len(ranks))
    hits = sum(1 for c in hole if c[0] in branks)
    strong = (hits >= 2) or (has_pair and (hits >= 1 or (max(ranks) if ranks else 0) >= 9))
    playable = strong or hits >= 1 or (max(ranks) if ranks else 0) >= 11

    if to_call <= 0:
        if strong and "raise" in legal:
            return legalize_action(req, "raise", int(req.get("opp_bet", 0)) + pot // 2)
        return legalize_action(req, "check")
    if strong and to_call <= pot:
        return legalize_action(req, "call")
    if playable and to_call <= pot * 0.35:
        return legalize_action(req, "call")
    return legalize_action(req, "check" if "check" in legal else "fold")


def choose_discard(req, state, time_left_ms, hands_played=0, total_hands=400):
    cards = req.get("hole_cards", state.hole)
    if not cards:
        return {"type": "discard", "card": "2s"}
    board_cards = req.get("board", [])

    if py_fallback is not None and len(board_cards) >= 3 and len(cards) >= 3 and time_left_ms > 1500:
        try:
            h_ids = [parse_card_id(c) for c in cards[:3]]
            b_ids = [parse_card_id(c) for c in board_cards[:3]]
            budget = _compute_dynamic_budget_ms(
                time_left_ms, hands_played, total_hands, int(req.get("pot", 6)), "flop", is_discard=True
            )
            drop_idx = py_fallback.py_choose_discard(h_ids, b_ids, state.dead, budget_ms=budget)
            if 0 <= drop_idx < len(cards):
                return {"type": "discard", "card": cards[drop_idx]}
        except Exception as e:
            sys.stderr.write(f"WARN: discard solver fallback ({e})\n")
            sys.stderr.flush()

    return {"type": "discard", "card": _fast_heuristic_discard(cards, board_cards)}


def choose_action(req, state, tracker, time_left_ms, score_cap, total_hands=400):
    legal = req.get("legal_actions", [])

    if py_fallback is None or not state.hole or time_left_ms < 350:
        return _fast_heuristic_action(req, state.hole)

    try:
        street_name = req.get("street", "preflop")
        street_id = STREET_MAP.get(street_name, 0)
        pot = int(req.get("pot", 2))
        my_bet = int(req.get("my_bet", 0))
        opp_bet = int(req.get("opp_bet", 0))
        to_call = int(req.get("to_call", max(0, opp_bet - my_bet)))
        min_raise = int(req.get("min_raise", 0))
        max_raise = int(req.get("max_raise", 0))

        opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose = tracker.get_stats()
        h_ids = [parse_card_id(c) for c in state.hole[:3]]
        b_ids = [parse_card_id(c) for c in req.get("board", [])]

        budget = 0.35 if time_left_ms < 1800 else _compute_dynamic_budget_ms(
            time_left_ms, tracker.hands, total_hands, pot, street_name, is_discard=False
        )

        act, amt = py_fallback.py_choose_action(
            street_id, pot, to_call, my_bet, opp_bet, min_raise, max_raise, legal,
            h_ids, b_ids, state.flop_board_ids, state.dead, state.opp_discard_id,
            opp_vpip, opp_agg, opp_fold_pre, opp_fold_post, opp_sd_loose,
            state.is_button, state.opp_raised, tracker.net_chips, score_cap,
            budget_ms=budget
        )
        return legalize_action(req, act, amt)
    except Exception as e:
        sys.stderr.write(f"WARN: action solver fallback ({e})\n")
        sys.stderr.flush()
        return _fast_heuristic_action(req, state.hole)


def main():
    gc.disable()
    current_state = LiveState()
    tracker = OpponentTracker()
    time_bank_ms = 60000.0
    total_spent_ms = 0.0
    total_hands = 400
    score_cap = 400

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        t0 = time.perf_counter()
        msg = None
        try:
            msg = json.loads(line)
            t = msg.get("type")
            reply = None

            if t == "init":
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
                total_hands = int(msg.get("total_hands", 1000 if time_bank_ms > 100000 else 400))
                score_cap = 1000 if (total_hands > 600 or time_bank_ms > 100000) else 400
            elif t == "new_hand":
                current_state.hole = list(msg.get("hole_cards", []))
                current_state.flop_board_ids = []
                current_state.dead = 0
                current_state.opp_discard_id = -1
                current_state.opp_raised = 0
                seat = msg.get("seat", msg.get("button"))
                if seat in ("button", "BTN", "SB", 0) and seat is not False:
                    current_state.is_button = 1
                elif seat in ("big_blind", "BB", 1) and seat is not True:
                    current_state.is_button = 0
                else:
                    current_state.is_button = 1 if (tracker.hands % 2 == 0) else 0
                if "time_bank_ms" in msg:
                    time_bank_ms = float(msg["time_bank_ms"])
                    if time_bank_ms > 100000 and total_hands <= 400:
                        total_hands = 1000
                        score_cap = 1000
            elif t == "action_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                board_cards = msg.get("board", [])
                if len(board_cards) == 3 and not current_state.flop_board_ids:
                    current_state.flop_board_ids = [parse_card_id(c) for c in board_cards]

                my_b = int(msg.get("my_bet", 0))
                opp_b = int(msg.get("opp_bet", 0))
                street = msg.get("street", "preflop")
                if street == "preflop":
                    if my_b == 1 and opp_b == 2:
                        current_state.is_button = 1
                    elif my_b == 2 and opp_b >= 2:
                        current_state.is_button = 0
                    if opp_b > 2:
                        current_state.opp_raised = 1
                else:
                    if opp_b > my_b:
                        current_state.opp_raised = 1

                reply = choose_action(
                    msg, current_state, tracker,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms)),
                    score_cap,
                    total_hands
                )
            elif t == "discard_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                board_cards = msg.get("board", [])
                if len(board_cards) == 3 and not current_state.flop_board_ids:
                    current_state.flop_board_ids = [parse_card_id(c) for c in board_cards]
                reply = choose_discard(
                    msg, current_state,
                    float(msg.get("time_left_ms", time_bank_ms - total_spent_ms)),
                    tracker.hands,
                    total_hands
                )
            elif t == "discard_result":
                my_discard = msg.get("my_discard")
                opp_discard = msg.get("opp_discard")
                if my_discard:
                    current_state.dead |= (1 << parse_card_id(my_discard))
                if opp_discard:
                    od_id = parse_card_id(opp_discard)
                    current_state.dead |= (1 << od_id)
                    current_state.opp_discard_id = od_id
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                elif my_discard:
                    current_state.hole = [c for c in current_state.hole if c != my_discard]
            elif t == "hand_result":
                tracker.update_from_result(msg)
                if tracker.hands % 50 == 0:
                    gc.collect()
            elif t == "match_end":
                break

            if reply is not None:
                sys.stdout.write(json.dumps(reply) + '\n')
                sys.stdout.flush()
            total_spent_ms += (time.perf_counter() - t0) * 1000.0

        except Exception as e:
            sys.stderr.write(f"ERROR: {str(e)}\n")
            sys.stderr.flush()
            if isinstance(msg, dict):
                mt = msg.get("type")
                if mt == "discard_request":
                    hc = msg.get("hole_cards", current_state.hole)
                    fb_card = _fast_heuristic_discard(hc, msg.get("board", [])) if hc else "2s"
                    sys.stdout.write(json.dumps({"type": "discard", "card": fb_card}) + '\n')
                    sys.stdout.flush()
                elif mt == "action_request":
                    fb = _fast_heuristic_action(msg, msg.get("hole_cards", current_state.hole))
                    sys.stdout.write(json.dumps(fb) + '\n')
                    sys.stdout.flush()
            elif '"discard_request"' in line:
                fallback_card = current_state.hole[0] if current_state.hole else "2s"
                sys.stdout.write(json.dumps({"type": "discard", "card": fallback_card}) + '\n')
                sys.stdout.flush()
            elif '"action_request"' in line:
                sys.stdout.write(json.dumps({"type": "action", "action": "fold"}) + '\n')
                sys.stdout.flush()
            total_spent_ms += (time.perf_counter() - t0) * 1000.0


if __name__ == "__main__":
    main()
