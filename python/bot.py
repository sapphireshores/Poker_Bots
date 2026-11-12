import sys
import os
import json
import gc
import time
import ctypes

RANKS = "23456789TJQKA"
SUIT_MAP = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
RANK_MAP = {r: i for i, r in enumerate(RANKS)}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(BASE_DIR, "libpoker_solver.so")
BIN_PATH = os.path.join(BASE_DIR, "tables.bin").encode("utf-8")

c_lib = None
if os.path.exists(LIB_PATH):
    c_lib = ctypes.CDLL(LIB_PATH)
    c_lib.py_init_engine.argtypes = [ctypes.c_char_p]
    c_lib.py_init_engine.restype = None

    c_lib.py_choose_discard.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint64,
        ctypes.c_double
    ]
    c_lib.py_choose_discard.restype = ctypes.c_int

    c_lib.py_choose_action.argtypes = [
        ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
        ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
        ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
        ctypes.c_uint64, ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    c_lib.py_choose_action.restype = None

    c_lib.py_init_engine(BIN_PATH)

class OpponentTracker:
    __slots__ = [
        'hands', 'vpip_count', 'opp_actions', 'opp_raises',
        'faced_bets', 'folded_to_bets'
    ]

    def __init__(self):
        self.hands = 25.0
        self.vpip_count = 25.0 * 0.55
        self.opp_actions = 40.0
        self.opp_raises = 40.0 * 0.25
        self.faced_bets = 25.0
        self.folded_to_bets = 25.0 * 0.40

    def update_from_history(self, history):
        if not history:
            return
        self.hands += 1.0
        opp_put_money = False
        hero_raised_last = False

        for entry in history:
            if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                actor = entry[1]
                act = entry[2]
            elif isinstance(entry, dict):
                actor = entry.get("actor", entry.get("player"))
                act = entry.get("action")
            else:
                continue

            is_opp = (actor in ("opp", 1, "B"))
            if is_opp:
                self.opp_actions += 1.0
                if act in ("call", "raise", "bet"):
                    opp_put_money = True
                if act in ("raise", "bet"):
                    self.opp_raises += 1.0
                if hero_raised_last:
                    self.faced_bets += 1.0
                    if act == "fold":
                        self.folded_to_bets += 1.0
                hero_raised_last = False
            else:
                hero_raised_last = (act in ("raise", "bet"))

        if opp_put_money:
            self.vpip_count += 1.0

    def stats(self):
        return (
            self.vpip_count / self.hands,
            self.opp_raises / self.opp_actions,
            self.folded_to_bets / self.faced_bets
        )

class LiveState:
    __slots__ = ['hole', 'board', 'dead', 'pot']

    def __init__(self):
        self.hole = []
        self.board = 0
        self.dead = 0
        self.pot = 0

def parse_card_id(card_str):
    return SUIT_MAP[card_str[1]] * 13 + RANK_MAP[card_str[0]]

def legalize_action(req, action, amount=None):
    legal = req.get("legal_actions", [])

    if action == "raise":
        if "raise" in legal and "min_raise" in req and "max_raise" in req:
            min_r = int(req["min_raise"])
            max_r = int(req["max_raise"])
            if min_r <= max_r:
                val = min_r if amount is None else max(min_r, min(max_r, int(amount)))
                return {"type": "action", "action": "raise", "amount": val}
        if "call" in legal:
            return {"type": "action", "action": "call"}
        if "check" in legal:
            return {"type": "action", "action": "check"}
        return {"type": "action", "action": "fold"}

    if action in legal:
        return {"type": "action", "action": action}

    if "check" in legal:
        return {"type": "action", "action": "check"}
    if "call" in legal:
        return {"type": "action", "action": "call"}
    if "fold" in legal:
        return {"type": "action", "action": "fold"}
    return {"type": "action", "action": legal[0]} if legal else {"type": "action", "action": "check"}

def choose_discard(req, state, time_left_ms):
    cards = list(req["hole_cards"]) if "hole_cards" in req else list(state.hole)
    if not cards:
        return {"type": "discard", "card": "2s"}
    if len(cards) < 3:
        return {"type": "discard", "card": cards[0]}

    board_cards = req.get("board", [])
    if c_lib is not None and len(board_cards) >= 3 and time_left_ms > 2000:
        hole_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in cards[:3]])
        board_arr = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in board_cards[:3]])
        drop_idx = int(c_lib.py_choose_discard(hole_arr, board_arr, state.dead, 12.0))
        if 0 <= drop_idx < len(cards):
            return {"type": "discard", "card": cards[drop_idx]}

    worst = min(cards, key=lambda c: RANK_MAP.get(c[0], -1))
    return {"type": "discard", "card": worst}

def choose_action(req, state, tracker, time_left_ms):
    legal = req.get("legal_actions", [])

    if time_left_ms < 2000 or c_lib is None or not state.hole:
        return legalize_action(req, "check" if "check" in legal else "call")

    hole_cards = state.hole
    hole_ids = (ctypes.c_uint8 * 3)(*[parse_card_id(c) for c in hole_cards[:3]] + [0] * (3 - len(hole_cards[:3])))
    street_map = {"preflop": 0, "flop": 1, "turn": 3, "river": 4}
    street_id = street_map.get(req.get("street", "flop"), 1)

    pot = int(req.get("pot", 2))
    my_stack = int(req.get("my_stack", 198))
    opp_stack = int(req.get("opp_stack", 198))
    my_bet = int(req.get("my_bet", 0))
    opp_bet = int(req.get("opp_bet", 0))
    min_r = int(req.get("min_raise", opp_bet + 2))
    last_raise = max(2, min_r - opp_bet)
    raises_left = int(req.get("raises_left", 3))

    opp_vpip, opp_agg, opp_fold = tracker.stats()

    out_action = ctypes.c_int(1)
    out_amount = ctypes.c_int(0)

    c_lib.py_choose_action(
        street_id, 0, raises_left,
        pot, my_stack, opp_stack, my_bet, opp_bet, last_raise,
        state.board, state.dead,
        hole_ids, len(hole_cards),
        8.0,
        opp_vpip, opp_agg, opp_fold,
        ctypes.byref(out_action), ctypes.byref(out_amount)
    )

    act_code = out_action.value
    if act_code == 0:
        return legalize_action(req, "fold")
    elif act_code == 2:
        return legalize_action(req, "raise", out_amount.value)
    else:
        return legalize_action(req, "check" if "check" in legal else "call")

def main():
    gc.disable()
    current_state = LiveState()
    tracker = OpponentTracker()
    time_bank_ms = 60000.0
    total_spent_ms = 0.0

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        t0 = time.perf_counter()
        try:
            msg = json.loads(line)
            t = msg.get("type")
            reply = None

            if t == "init":
                time_bank_ms = float(msg.get("time_bank_ms", 60000))
            elif t in ("hand_start", "new_hand"):
                current_state = LiveState()
                current_state.hole = list(msg.get("hole_cards", []))
            elif t == "action_request":
                current_state.pot = msg.get("pot", 0)
                current_state.board = 0
                for c in msg.get("board", []):
                    current_state.board |= (1 << parse_card_id(c))
                reply = choose_action(msg, current_state, tracker, time_bank_ms - total_spent_ms)
            elif t == "discard_request":
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                current_state.board = 0
                for c in msg.get("board", []):
                    current_state.board |= (1 << parse_card_id(c))
                reply = choose_discard(msg, current_state, time_bank_ms - total_spent_ms)
            elif t == "discard_result":
                my_discard = msg.get("my_discard")
                opp_discard = msg.get("opp_discard")
                if my_discard:
                    current_state.dead |= (1 << parse_card_id(my_discard))
                if opp_discard:
                    current_state.dead |= (1 << parse_card_id(opp_discard))
                if "hole_cards" in msg:
                    current_state.hole = list(msg["hole_cards"])
                elif my_discard:
                    current_state.hole = [c for c in current_state.hole if c != my_discard]
            elif t == "hand_result":
                tracker.update_from_history(msg.get("history", []))
            elif t == "notice":
                sys.stderr.write(f"NOTICE: {json.dumps(msg)}\n")
                sys.stderr.flush()
            elif t == "match_end":
                break

            if reply:
                sys.stdout.write(json.dumps(reply) + '\n')
                sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"ERROR: {str(e)}\n")
            sys.stderr.flush()
            if '"discard_request"' in line:
                fallback_card = current_state.hole[0] if current_state.hole else "2s"
                sys.stdout.write(json.dumps({"type": "discard", "card": fallback_card}) + '\n')
            else:
                sys.stdout.write(json.dumps({"type": "action", "action": "fold"}) + '\n')
            sys.stdout.flush()
        finally:
            total_spent_ms += (time.perf_counter() - t0) * 1000.0

if __name__ == '__main__':
    main()