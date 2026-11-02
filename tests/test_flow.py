"""End to end on a temp copy of one level: show, backup, edit, result, log, refusals."""
import glob, hashlib, json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import trimmer, pbslot

tmp = tempfile.mkdtemp(); saves = os.path.join(tmp, "saves"); bak = os.path.join(tmp, "bak")
shutil.copytree(os.path.join(trimmer.SAVE_ROOT, "181"), os.path.join(saves, "181"))
env = dict(os.environ, PB_SAVES=saves, PB_BACKUPS=bak, PB_LOG=os.path.join(tmp, "r.jsonl"), PYTHONIOENCODING="utf8")
def pb(*a, e=env):
    return subprocess.run([sys.executable, os.path.join(ROOT, "pb.py"), *a], capture_output=True, text=True, env=e)
def sums():
    return {os.path.basename(p): hashlib.md5(open(p, "rb").read()).hexdigest() for p in glob.glob(os.path.join(saves, "181", "*"))}

before = sums()
r = pb("show", "181", "Claude v2"); assert r.returncode == 0 and "len" in r.stdout, r.stderr
wood = next(l.split()[0] for l in r.stdout.splitlines()[1:] if " Wood " in l)
r = pb("edit", "181", "Claude v2", "Try 1", "--remove", wood); print(r.stdout, r.stderr[-300:])
after = sums()
assert {k: after[k] for k in before} == before, "existing save changed"
assert "Try 1.slot" in after
a = pbslot.parse(os.path.join(saves, "181", "Claude v2.slot")); c = pbslot.parse(os.path.join(saves, "181", "Try 1.slot"))
assert len(c["edges"]) == len(a["edges"]) - 1
copies = {os.path.basename(p): hashlib.md5(open(p, "rb").read()).hexdigest() for p in glob.glob(os.path.join(bak, "181", "*", "*"))}
assert copies == before, "backup incomplete"
r = pb("edit", "181", "Claude v2", "Try 1", "--remove", wood); assert r.returncode and "already exists" in r.stderr
assert pb("result", "181", "Try 1", "fail", "120.5", "left leg").returncode == 0
rows = [json.loads(l) for l in pb("log", "181").stdout.splitlines()]
assert rows[-1]["slot"] == "Try 1" and rows[-1]["outcome"] == "fail" and rows[-1]["stress"] == "120.5"
assert pb("result", "181", "Try 1", "maybe").returncode, "bad outcome accepted"
blocked = os.path.join(tmp, "file"); open(blocked, "w").close()
r = pb("edit", "181", "Claude v2", "Try 2", "--remove", wood, e=dict(env, PB_BACKUPS=blocked))
assert r.returncode and "Try 2.slot" not in sums(), "wrote without a backup"
print("ALL PASSED")
