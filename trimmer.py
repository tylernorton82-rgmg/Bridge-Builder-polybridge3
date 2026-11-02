"""Stress estimate and cost trimmer for Poly Bridge 3 slots.
Only ever deletes pieces or swaps steel to wood on existing joints, so it can't
create a joint in an illegal spot. Input slots are never modified."""
import math, os, copy, re, struct
import pbslot, truss

ROAD, WOOD, STEEL = 1, 3, 4
PRICE = {1: 300, 2: 400, 3: 180, 4: 450, 5: 750, 6: 220, 7: 220}
PCT0 = {1: 1.69, 2: 1.5, 3: 1.8, 4: 0.905, 5: 0.905, 6: 1.0, 7: 1.0}
NAMES = {1: "Road", 2: "Reinforced road", 3: "Wood", 4: "Steel", 5: "Hydraulic", 6: "Rope", 7: "Cable"}
WOOD_MAX = 2.02
SAVE_ROOT = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\Dry Cactus\Poly Bridge 3\Profiles\Default\SaveSlots")

def load(path):
    br = pbslot.parse(path)
    A = {a["id"]: (a["x"], a["y"]) for a in pbslot.anchors(br)}
    J = {j["id"]: (j["x"], j["y"]) for j in br["joints"]}
    return {"path": path, "br": br, "A": A, "J": J, "P": {**J, **A}, "level": level_of(path)}

def level_of(path):
    m = re.fullmatch(r"\d{3}", os.path.basename(os.path.dirname(path)))
    return int(m.group()) if m else None

def length(b, e):
    return math.dist(b["P"][e["a"]], b["P"][e["b"]])

def cost(b, edges=None):
    return sum(PRICE.get(e["mat"], 0) * length(b, e) for e in (b["br"]["edges"] if edges is None else edges))

def stress(b, edges=None, scale=1.0):
    """per-piece estimated % (list), or None if the bridge would fall apart"""
    edges = b["br"]["edges"] if edges is None else edges
    used = {n for e in edges for n in (e["a"], e["b"])}
    J = {k: v for k, v in b["J"].items() if k in used}
    env, mech = truss.solve(J, b["A"], [(e["a"], e["b"], e["mat"]) for e in edges])
    return None if mech else [v * PCT0.get(e["mat"], 1.0) * scale for v, e in zip(env, edges)]

def warnings(b):
    w = []
    if any(e["mat"] in (5, 6, 7) for e in b["br"]["edges"]):
        w.append("Has hydraulics, rope or cable: those pieces are left alone and moving parts aren't simulated.")
    return w

def trim(b, target=90.0, observed=None, nlock=6, progress=None, stop=None):
    """Returns (edges, est %, log). observed = the max stress % the game showed."""
    edges = copy.deepcopy(b["br"]["edges"])
    u = stress(b, edges)
    if u is None: raise ValueError("The solver sees this bridge as unstable, so it can't be trimmed safely.")
    scale = observed / max(u) if observed else 1.0
    u = [v * scale for v in u]
    moving = {n for e in edges if e["mat"] in (5, 6, 7) for n in (e["a"], e["b"])}
    flagged = {j["id"] for j in b["br"]["joints"] if any(j["flags"])}
    steel = sorted((i for i, e in enumerate(edges) if e["mat"] == STEEL), key=lambda i: -u[i])
    locked = {edges[i]["id"] for i in steel[:nlock]}
    log = []
    while True:
        if stop and stop(): break
        opts = []
        for e in edges:
            if e["mat"] not in (WOOD, STEEL) or e["id"] in locked: continue
            if e["a"] in moving or e["b"] in moving or e["a"] in flagged or e["b"] in flagged: continue
            L = length(b, e)
            opts.append((PRICE[e["mat"]] * L, e, None))
            if e["mat"] == STEEL and L <= WOOD_MAX: opts.append(((PRICE[STEEL] - PRICE[WOOD]) * L, e, WOOD))
        opts.sort(key=lambda o: -o[0])
        for k, (save, e, new) in enumerate(opts):
            if progress: progress(len(log), k, len(opts))
            if stop and stop(): break
            t = [dict(x, mat=new) if x["id"] == e["id"] else x for x in edges] if new else [x for x in edges if x["id"] != e["id"]]
            s = stress(b, t, scale)
            if s is not None and max(s) <= target:
                edges = t; log.append(("Steel to wood" if new else "Removed " + NAMES[e["mat"]].lower(), save)); break
        else:
            break
    final = stress(b, edges, scale)
    return edges, max(final), log

def auto_build(b, limit=90.0, height=1.75):
    """New bridge from the save's anchors: straight road between the outermost anchors with a truss
    above it, so nothing sits low where terrain usually is. Pieces are wood, upgraded to steel as needed."""
    if b["br"].get("edges") and any(e["mat"] in (5, 6, 7) for e in b["br"]["edges"]):
        raise ValueError("This save has hydraulics, rope or cable. Use a save with just one road piece.")
    A = b["A"]
    if len(A) < 2: raise ValueError("This save has fewer than two anchors.")
    left = max(A, key=lambda i: (-round(A[i][0], 1), A[i][1])); right = max(A, key=lambda i: (round(A[i][0], 1), A[i][1]))
    (x0, y0), (x1, y1) = A[left], A[right]; L = math.dist(A[left], A[right])
    n = math.ceil(L / 1.95); nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    J, joints, edges = dict(A), {}, []
    def joint(p):
        i = pbslot.new_id(); J[i] = p; joints[i] = p; return i
    def edge(a, c, m):
        edges.append({"mat": m, "a": a, "b": c, "u": (1, 0, 0), "id": pbslot.new_id()})
    road = [left] + [joint((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)) for k in range(1, n)] + [right]
    top = [joint((x0 + (x1 - x0) * (k + .5) / n + nx * height, y0 + (y1 - y0) * (k + .5) / n + ny * height)) for k in range(n)]
    for a, c in zip(road, road[1:]): edge(a, c, ROAD)
    for k, q in enumerate(top):
        edge(road[k], q, WOOD); edge(q, road[k + 1], WOOD)
    for a, c in zip(top, top[1:]): edge(a, c, WOOD)
    br = copy.deepcopy(b["br"]); br["edges"] = edges
    br["joints"] = [{"x": p[0], "y": p[1], "z": 0.0, "flags": (0, 0, 0), "id": i} for i, p in joints.items()]
    nb = {**b, "br": br, "J": joints, "P": J}
    for _ in range(len(edges)):
        u = stress(nb)
        if u is None: raise ValueError("Couldn't make a stable bridge from these anchors.")
        w = max(range(len(edges)), key=lambda i: u[i])
        if u[w] <= limit or edges[w]["mat"] != WOOD: break
        edges[w]["mat"] = STEEL
    return nb, max(stress(nb))

def saved_cost(path):
    """the m_Budget number stored in the slot (pieces plus foundations)"""
    d = open(path, "rb").read(); k = "m_Budget".encode("utf-16-le"); i = d.find(k)
    return struct.unpack_from("<i", d, i + len(k))[0] if i >= 0 else 0

def free_path(b, name):
    return os.path.join(os.path.dirname(b["path"]), name + ".slot")

def save_new(b, edges, name):
    """Writes a brand-new slot next to the original. Refuses to replace anything."""
    if not re.fullmatch(r"[A-Za-z0-9 _()-]{1,40}", name): raise ValueError("Use letters, numbers and spaces in the name.")
    out = free_path(b, name)
    if os.path.exists(out): raise FileExistsError(f'"{name}" already exists. Pick another name.')
    used = {n for e in edges for n in (e["a"], e["b"])}
    nb = copy.deepcopy(b["br"])
    nb["joints"] = [j for j in nb["joints"] if j["id"] in used]
    nb["edges"] = copy.deepcopy(edges)
    extra = max(0, saved_cost(b["path"]) - cost(b))             # foundations stay in the total
    pbslot.write_slot(b["path"], nb, out, name, cost(b, edges) + extra)
    return out
