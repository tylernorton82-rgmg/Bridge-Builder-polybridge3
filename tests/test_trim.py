import os, sys, shutil, glob, tempfile, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import trimmer, pbslot
tmp = tempfile.mkdtemp()
for lvl in sys.argv[1:] or ["115", "181", "112", "107"]:
    src = os.path.join(trimmer.SAVE_ROOT, lvl)
    d = os.path.join(tmp, lvl); os.makedirs(d)
    for f in glob.glob(src + "/*.slot")[:4]:
        p = shutil.copy(f, d); h = hashlib.md5(open(p, "rb").read()).digest()
        b = trimmer.load(p); t = time.time()
        try: E, s, log = trimmer.trim(b, 90)
        except Exception as x: print(lvl, os.path.basename(f), "SKIP", x); continue
        o = trimmer.save_new(b, E, "App test"); r = pbslot.parse(o)
        assert [(e["a"], e["b"], e["mat"]) for e in r["edges"]] == [(e["a"], e["b"], e["mat"]) for e in E]
        assert {j["id"] for j in r["joints"]} <= {j["id"] for j in b["br"]["joints"]}
        assert hashlib.md5(open(p, "rb").read()).digest() == h
        try: trimmer.save_new(b, E, "App test"); raise SystemExit("OVERWROTE")
        except FileExistsError: pass
        os.remove(o)
        print(lvl, os.path.basename(f), f"${trimmer.cost(b):,.0f} -> ${trimmer.cost(b,E):,.0f} est {s:.0f}% moves {len(log)} {time.time()-t:.1f}s")
