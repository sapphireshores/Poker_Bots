"""Example opponent for local testing: plays random legal actions and discards."""
import sys, json, random

def choose_action(req):
    legal = req["legal_actions"]
    roll = random.random()
    if "raise" in legal and roll < 0.2:
        size = random.choice((0.5, 0.75, 1.0, 2.0))
        target = req["opp_bet"] + int(size * (req["pot"] + req["to_call"]))
        amount = max(req["min_raise"], min(req["max_raise"], target))
        return {"type": "action", "action": "raise", "amount": amount}
    if "check" in legal:
        return {"type": "action", "action": "check"}
    if roll < 0.8:
        return {"type": "action", "action": "call"}
    return {"type": "action", "action": "fold"}

def choose_discard(req):
    return {"type": "discard", "card": random.choice(req["hole_cards"])}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        t = msg.get("type")
        if t == "action_request":
            reply = choose_action(msg)
        elif t == "discard_request":
            reply = choose_discard(msg)
        elif t == "match_end":
            break
        else:
            continue
        print(json.dumps(reply), flush=True)

if __name__ == "__main__":
    main()