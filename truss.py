"""Tiny 2D truss solver (pin joints, axial members, anchors fixed).

Loads: self-weight of members (per metre, by material) + a vehicle point load
moved along the road joints; returns the envelope of |axial force| per member.
Absolute forces are uncalibrated -- compare designs as ratios against one the
user has tested (e.g. "user's bridge = 73%").
"""
import math
import numpy as np

EA = {1: 4e5, 2: 5e5, 3: 2e5, 4: 6e5, 5: 6e5, 6: 1.5e5, 7: 3e5}   # relative axial stiffness (guess; 6 rope, 7 cable)
WPM = {1: 1.0, 2: 1.2, 3: 0.5, 4: 0.7, 5: 0.9, 6: 0.15, 7: 0.25}   # relative weight per metre (guess)
VEHICLE = 12.0                       # relative vehicle weight (guess)
import os as _os
REG = float(_os.environ.get("TRUSS_REG", 0))   # e.g. 50: tiny stiffness at every joint


def solve(joints, anchors, edges, vehicle=VEHICLE):
    """joints/anchors: {id: (x, y)}; edges: list of (a, b, mat).
    Returns (forces_envelope list, mechanism bool)."""
    free = list(joints)
    idx = {j: i for i, j in enumerate(free)}
    P = dict(joints); P.update(anchors)
    n = 2 * len(free)
    K = np.zeros((n, n))
    geo = []
    for a, b, m in edges:
        (xa, ya), (xb, yb) = P[a], P[b]
        L = math.hypot(xb - xa, yb - ya); c, s = (xb - xa) / L, (yb - ya) / L
        k = EA[m] / L
        geo.append((a, b, m, L, c, s, k))
        dofs = [(a, 0), (a, 1), (b, 0), (b, 1)]
        v = np.array([-c, -s, c, s])
        for i, (ji, di) in enumerate(dofs):
            if ji not in idx: continue
            for j, (jj, dj) in enumerate(dofs):
                if jj not in idx: continue
                K[2 * idx[ji] + di, 2 * idx[jj] + dj] += k * v[i] * v[j]
    if REG: K += np.eye(n) * REG          # weak ground springs (lets near-mechanisms be analysed)
    # mechanism check
    cond = np.linalg.cond(K) if n else 0
    if not np.isfinite(cond) or cond > 1e12:
        return None, True
    base = np.zeros(n)
    for a, b, m, L, c, s, k in geo:
        w = WPM[m] * L / 2
        for j in (a, b):
            if j in idx: base[2 * idx[j] + 1] -= w
    road_joints = sorted({j for a, b, m in edges if m == 1 for j in (a, b) if j in idx}, key=lambda j: P[j][0])
    env = np.zeros(len(geo)); comp = np.zeros(len(geo))
    for rj in [None] + road_joints:
        f = base.copy()
        if rj: f[2 * idx[rj] + 1] -= vehicle
        u = np.linalg.solve(K, f)
        for i, (a, b, m, L, c, s, k) in enumerate(geo):
            ua = u[2 * idx[a]:2 * idx[a] + 2] if a in idx else np.zeros(2)
            ub = u[2 * idx[b]:2 * idx[b] + 2] if b in idx else np.zeros(2)
            f_ax = k * ((ub - ua) @ np.array([c, s]))   # + tension, - compression
            env[i] = max(env[i], abs(f_ax)); comp[i] = min(comp[i], f_ax)
    solve.last_comp = comp
    return env, False


def from_slot(br, anchors_list):
    J = {j["id"]: (j["x"], j["y"]) for j in br["joints"]}
    A = {a["id"]: (a["x"], a["y"]) for a in anchors_list}
    E = [(e["a"], e["b"], e["mat"]) for e in br["edges"]]
    return J, A, E
