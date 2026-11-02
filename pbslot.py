"""Read Poly Bridge 3 .slot files (Odin-serialized BridgeSaveSlotData).

The m_Bridge field is a byte blob:
  i32 ?, i32 version (18), i32 n_joints,
  joint  = f32 x, f32 y, f32 z, u8, u8, str guid, u8      (metres)
  i32 n_edges,
  edge   = i32 material, str joint_a, str joint_b, i32, i32, i32, str guid
  ... (rest not decoded yet)
str = i16 length + ASCII.
Joint guids that aren't in the joint list are the level's built-in anchors.

Usage: py pbslot.py <file.slot>
"""
import struct, sys


class R:
    def __init__(self, b, p=0):
        self.b, self.p = b, p
    def i32(self):
        v = struct.unpack_from("<i", self.b, self.p)[0]; self.p += 4; return v
    def f32(self):
        v = struct.unpack_from("<f", self.b, self.p)[0]; self.p += 4; return v
    def u8(self):
        v = self.b[self.p]; self.p += 1; return v
    def s(self):
        n = struct.unpack_from("<h", self.b, self.p)[0]; self.p += 2
        v = self.b[self.p:self.p + n].decode("ascii"); self.p += n; return v


def bridge_blob(data):
    i = data.find("m_Bridge".encode("utf-16le"))
    j = data.find("mscorlib".encode("utf-16le"), i) + 16
    n = struct.unpack_from("<i", data, j + 5)[0]
    return j + 9, data[j + 9:j + 9 + n]


def parse(path):
    data = open(path, "rb").read()
    off, b = bridge_blob(data)
    r = R(b)
    head, ver, nj = r.i32(), r.i32(), r.i32()
    joints = []
    for _ in range(nj):
        x, y, z = r.f32(), r.f32(), r.f32()
        f1, f2 = r.u8(), r.u8()
        g = r.s()
        f3 = r.u8()
        joints.append({"x": x, "y": y, "z": z, "flags": (f1, f2, f3), "id": g})
    ne = r.i32()
    edges = []
    for _ in range(ne):
        m = r.i32(); a = r.s(); bb = r.s()
        u = (r.i32(), r.i32(), r.i32())
        g = r.s()
        edges.append({"mat": m, "a": a, "b": bb, "u": u, "id": g})
    return {"version": ver, "head": head, "joints": joints, "edges": edges,
            "rest_at": r.p, "blob_len": len(b), "blob": b}


if __name__ == "__main__":
    br = parse(sys.argv[1])
    print(f"version {br['version']}  joints {len(br['joints'])}  edges {len(br['edges'])}  "
          f"undecoded tail {br['blob_len'] - br['rest_at']} bytes")
    known = {j["id"] for j in br["joints"]}
    from collections import Counter
    print("materials:", Counter(e["mat"] for e in br["edges"]))
    print("flags u:", Counter(e["u"] for e in br["edges"]))
    print("anchor ids used:", sorted({e[k] for e in br["edges"] for k in "ab"} - known))
    print("tail:", br["blob"][br["rest_at"]:br["rest_at"] + 160].hex(" "))


def anchors_scan(br):
    """Anchor records sit in the tail in joint format (x,y,z,u8,u8,str,u8).
    Locate them by scanning for i16-length-prefixed ids preceded by 3 floats."""
    b, p, out = br["blob"], br["rest_at"], []
    while p < len(b) - 20:
        n = struct.unpack_from("<h", b, p)[0]
        if 18 <= n <= 40 and p + 2 + n <= len(b):
            s = b[p + 2:p + 2 + n]
            if all(48 <= c < 123 or c == 45 for c in s) and p >= 14:
                x, y, z = struct.unpack_from("<fff", b, p - 14)
                if abs(z) < 1e-6 and -500 < x < 500 and -500 < y < 500:
                    out.append({"x": x, "y": y, "id": s.decode()})
                    p += 2 + n
                    continue
        p += 1
    return out


# ---------------- writing ----------------
import random, string

def _s(v):
    b = v.encode("ascii")
    return struct.pack("<h", len(b)) + b

def new_id():
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(22))

def build_blob(br):
    out = [struct.pack("<iii", br["head"], br["version"], len(br["joints"]))]
    for j in br["joints"]:
        f1, f2, f3 = j.get("flags", (0, 0, 0))
        out.append(struct.pack("<fffBB", j["x"], j["y"], j.get("z", 0.0), f1, f2) + _s(j["id"]) + bytes([f3]))
    out.append(struct.pack("<i", len(br["edges"])))
    for e in br["edges"]:
        out.append(struct.pack("<i", e["mat"]) + _s(e["a"]) + _s(e["b"]) +
                   struct.pack("<iii", *e.get("u", (1, 0, 0))) + _s(e["id"]))
    out.append(br["blob"][br["rest_at"]:])   # tail (anchors etc.) copied verbatim
    return b"".join(out)

def _replace_str_field(data, field, value):
    """Odin string value: after the utf-16 field name -> 0x01, i32 nchars, utf-16 chars."""
    k = field.encode("utf-16le")
    i = data.find(k) + len(k)
    assert data[i] == 1, (field, data[i:i+8].hex())
    n = struct.unpack_from("<i", data, i + 1)[0]
    end = i + 5 + 2 * n
    return data[:i + 1] + struct.pack("<i", len(value)) + value.encode("utf-16le") + data[end:]

def _set_i32_field(data, field, v):
    k = field.encode("utf-16le")
    i = data.find(k) + len(k)
    return data[:i] + struct.pack("<i", v) + data[i + 4:]

def write_slot(template_path, br, out_path, display_name, cost):
    data = open(template_path, "rb").read()
    off, old = bridge_blob(data)
    blob = build_blob(br)
    data = data[:off - 4] + struct.pack("<i", len(blob)) + blob + data[off + len(old):]
    fname = out_path.replace("\\", "/").split("/")[-1]
    data = _replace_str_field(data, "m_DisplayName", display_name)
    data = _replace_str_field(data, "m_SlotFilename", fname)
    data = _set_i32_field(data, "m_Budget", int(round(cost)))
    data = _set_i32_field(data, "m_SlotID", 10)   # 10 = user-named save (0 auto, 2/3 = Lowest slots)
    open(out_path, "wb").write(data)


# ---------------- foundations (BridgePillar) ----------------
def _anchor_rec(x, y, i):
    return struct.pack("<fffBB", x, y, 0.0, 1, 0) + _s(i) + b"\x00"

def set_foundations(br, level_anchors, foundations):
    """Rewrite the blob tail: 12-byte prefix, anchor list (level anchors + one
    per foundation top), pillar list, then the list of pillar-top anchors.
    level_anchors: [(x, y, id)]; foundations: [(x, top_y)] (base at y=0).
    Returns ids of the new top anchors."""
    tail = br["blob"][br["rest_at"]:]
    prefix = tail[:12]
    tops = []
    allA = list(level_anchors)
    for x, top in foundations:
        i = new_id(); tops.append((x, top, i)); allA.append((x, top, i))
    out = [prefix, struct.pack("<i", len(allA))]
    out += [_anchor_rec(x, y, i) for x, y, i in allA]
    out.append(struct.pack("<i", len(tops)))
    for x, top, i in tops:
        out.append(struct.pack("<ffff", x, 0.0, 0.0, top) + _s("BridgePillar") + _s(new_id()[:20]) + _s(i) + b"\x00\x00\x00\x00")
    out.append(struct.pack("<i", len(tops)))
    out += [_anchor_rec(x, y, i) for x, y, i in tops]
    br["blob"] = br["blob"][:br["rest_at"]] + b"".join(out)
    return [i for _, _, i in tops]


def _try_anchor_list(b, p):
    """count (i32) followed by exactly `count` anchor records: f32 x,y,z(=0), u8 1, u8 0, str id, u8."""
    try:
        n = struct.unpack_from("<i", b, p)[0]
        if not 1 <= n <= 64: return None
        q = p + 4; out = []
        for _ in range(n):
            x, y, z = struct.unpack_from("<fff", b, q); q += 12
            f1, f2 = b[q], b[q + 1]; q += 2
            L = struct.unpack_from("<h", b, q)[0]; q += 2
            if not (abs(z) < 1e-6 and f1 == 1 and 18 <= L <= 40 and abs(x) < 1000 and abs(y) < 1000): return None
            sid = b[q:q + L]
            if not all(48 <= c < 123 or c == 45 for c in sid): return None
            q += L + 1
            out.append({"x": x, "y": y, "id": sid.decode()})
        return out, q
    except struct.error:
        return None

def anchors(br):
    """Structured parse of the level anchor list in the blob tail (first valid count+records run).
    Falls back to the old heuristic scan if nothing parses."""
    b = br["blob"]
    for p in range(br["rest_at"], len(b) - 8):
        r = _try_anchor_list(b, p)
        if r: return r[0]
    return anchors_scan(br)


# ---------------- hydraulics block (blob tail, version 18) ----------------
def parse_hyd(br):
    """Tail layout on hydraulic levels:
      i32 head, i32 nHyd, nHyd x [f32 value, str jointA, str jointB, str controllerId],
      i32 nPhases, nPhases x [str phaseId, i32 n, n x str controllerId,
                              i32 m, m x (str splitJointOrAnchorId, i32 v), u8 flag],
      <anchor list ...>   (returned as 'rest')"""
    r = R(br["blob"], br["rest_at"])
    head = r.i32(); n = r.i32()
    hyd = [{"val": r.f32(), "a": r.s(), "b": r.s(), "ctl": r.s()} for _ in range(n)]
    nph = r.i32(); phases = []
    for _ in range(nph):
        pid = r.s(); k = r.i32(); ctl = [r.s() for _ in range(k)]
        m = r.i32(); split = [(r.s(), r.i32()) for _ in range(m)]
        phases.append({"id": pid, "ctl": ctl, "split": split, "flag": r.u8()})
    return {"head": head, "hyd": hyd, "phases": phases, "rest": br["blob"][r.p:]}

def build_hyd(h):
    out = [struct.pack("<ii", h["head"], len(h["hyd"]))]
    for x in h["hyd"]:
        out.append(struct.pack("<f", x["val"]) + _s(x["a"]) + _s(x["b"]) + _s(x["ctl"]))
    out.append(struct.pack("<i", len(h["phases"])))
    for ph in h["phases"]:
        out.append(_s(ph["id"]) + struct.pack("<i", len(ph["ctl"])) + b"".join(_s(c) for c in ph["ctl"]))
        out.append(struct.pack("<i", len(ph["split"])) + b"".join(_s(a) + struct.pack("<i", v) for a, v in ph["split"]))
        out.append(bytes([ph["flag"]]))
    out.append(h["rest"])
    return b"".join(out)

def set_hyd(br, h):
    br["blob"] = br["blob"][:br["rest_at"]] + build_hyd(h)


# ---------------- foundations on hydraulic levels (inside parse_hyd()['rest']) ----------------
def parse_found_rest(rest):
    """rest = anchor list, pillar list, pillar-top anchor list, trailing bytes."""
    r = R(rest)
    def anchor_rec():
        x, y, z = r.f32(), r.f32(), r.f32(); f1, f2 = r.u8(), r.u8(); i = r.s(); t = r.u8()
        return {"x": x, "y": y, "z": z, "f1": f1, "f2": f2, "id": i, "t": t}
    n = r.i32(); anchors = [anchor_rec() for _ in range(n)]
    npil = r.i32(); pillars = []
    for _ in range(npil):
        x, y, z, top = r.f32(), r.f32(), r.f32(), r.f32()
        kind = r.s(); pid = r.s(); aid = r.s(); extra = r.i32()
        pillars.append({"x": x, "y": y, "z": z, "top": top, "kind": kind, "pid": pid, "aid": aid, "extra": extra})
    nt = r.i32(); tops = [anchor_rec() for _ in range(nt)]
    return {"anchors": anchors, "pillars": pillars, "tops": tops, "trail": rest[r.p:]}

def build_found_rest(fr):
    def arec(a): return struct.pack("<fffBB", a["x"], a["y"], a["z"], a["f1"], a["f2"]) + _s(a["id"]) + bytes([a["t"]])
    out = [struct.pack("<i", len(fr["anchors"]))] + [arec(a) for a in fr["anchors"]]
    out.append(struct.pack("<i", len(fr["pillars"])))
    for p in fr["pillars"]:
        out.append(struct.pack("<ffff", p["x"], p["y"], p["z"], p["top"]) + _s(p["kind"]) + _s(p["pid"]) + _s(p["aid"]) + struct.pack("<i", p["extra"]))
    out.append(struct.pack("<i", len(fr["tops"]))); out += [arec(a) for a in fr["tops"]]
    out.append(fr["trail"])
    return b"".join(out)
