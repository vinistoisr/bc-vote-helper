"""Random-voter share per region for the V2 spec.

Usage: python -I sim_random_voters.py [N]
For each region, N voters pick a random option on each of that region's 16
questions (13 provincial + 3 local) at medium importance. Reports the share
whose top party is each party (ties split equally) and flags any party above 35%.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTIES = ["ndp", "conservative", "green", "centrebc", "onebc"]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    spec = json.load(open(os.path.join(HERE, "quiz_spec.json"), encoding="utf-8"))
    qs = {q["id"]: q for q in spec["questions"]}
    provincial = [q for q in spec["questions"] if q["scope"] == "provincial"]
    rng = random.Random(2026)
    for reg in spec["regions"]:
        local = [qs[i] for i in reg["local_qids"]]
        battery = provincial + local
        wins = {p: 0.0 for p in PARTIES}
        for _ in range(n):
            num = {p: 0.0 for p in PARTIES}
            den = {p: 0.0 for p in PARTIES}
            for q in battery:
                opt = rng.choice(q["options"])
                for p in PARTIES:
                    if q["party_positions"][p].get("no_position"):
                        continue
                    num[p] += opt["scores"][p]
                    den[p] += 4
            pct = {p: (num[p] / den[p] if den[p] else 0.0) for p in PARTIES}
            best = max(pct.values())
            top = [p for p in PARTIES if pct[p] == best]
            for p in top:
                wins[p] += 1.0 / len(top)
        shares = {p: 100.0 * wins[p] / n for p in PARTIES}
        flag = [p for p in PARTIES if shares[p] > 35]
        print(f"{reg['id']:14s} ({len(battery)} q): " +
              ", ".join(f"{p} {shares[p]:5.1f}%" for p in PARTIES) +
              (f"   FLAG >35%: {flag}" if flag else ""))


if __name__ == "__main__":
    main()
