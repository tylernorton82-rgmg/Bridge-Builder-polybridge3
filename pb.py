"""Command tools for Claude Code. Saves are backed up before every write. Results from the game are logged so each try learns from the last.
  py pb.py show 181 "Claude v2"
  py pb.py edit 181 "Claude v2" "Try 1" --remove 12,13 --wood 7
  py pb.py result 181 "Try 1" pass 95.69 "note"
  py pb.py log 181"""
import json, os, sys, time
import trimmer

LOG = os.environ.get("PB_LOG") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.jsonl")

def slot(level, name):
    return trimmer.load(os.path.join(trimmer.SAVE_ROOT, f"{int(level):03d}", name + ".slot"))

def ids(v):
    return {int(x) for x in v.split(",") if x}

def show(level, name):
    b = slot(level, name); E = b["br"]["edges"]; u = trimmer.stress(b)
    print(f"estimated pieces ${trimmer.cost(b):,.0f}  estimated total ${trimmer.saved_cost(b['path']):,}  anchors {sorted(b['A'].values())}")
    for i, e in enumerate(E):
        pa, pc = b["P"][e["a"]], b["P"][e["b"]]
        print(f"{i:3d} {trimmer.NAMES.get(e['mat'], e['mat']):10s} ({pa[0]:.2f},{pa[1]:.2f})-({pc[0]:.2f},{pc[1]:.2f}) len {trimmer.length(b, e):.2f} model est {u[i] if u else 0:.0f}")

def edit(level, name, new, args):
    b = slot(level, name); rm, wood, steel = set(), set(), set()
    for k, v in zip(args[::2], args[1::2]):
        if k == "--remove": rm = ids(v)
        elif k == "--wood": wood = ids(v)
        elif k == "--steel": steel = ids(v)
        else: sys.exit("unknown option " + k)
    E = []
    for i, e in enumerate(b["br"]["edges"]):
        if i in rm: continue
        if i in wood:
            if e["mat"] != trimmer.STEEL or trimmer.length(b, e) > trimmer.WOOD_MAX: sys.exit(f"piece {i} can't become wood")
            e = dict(e, mat=trimmer.WOOD)
        if i in steel:
            if e["mat"] != trimmer.WOOD: sys.exit(f"piece {i} is not wood")
            e = dict(e, mat=trimmer.STEEL)
        E.append(e)
    if trimmer.stress(b, E) is None: sys.exit("that change makes the bridge unstable")
    print("wrote", trimmer.save_new(b, E, new), f"pieces ${trimmer.cost(b, E):,.0f}")

def result(level, name, outcome, stress=None, note=""):
    if outcome not in ("pass", "fail"): sys.exit("outcome must be pass or fail")
    with open(LOG, "a") as f:
        f.write(json.dumps({"t": int(time.time()), "level": int(level), "slot": name, "outcome": outcome, "stress": stress, "note": note}) + "\n")

def log(level):
    if os.path.exists(LOG):
        for l in open(LOG):
            if json.loads(l)["level"] == int(level): print(l.strip())

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "edit": edit(a[1], a[2], a[3], a[4:])
    else: {"show": show, "result": result, "log": log}[a[0]](*a[1:])
