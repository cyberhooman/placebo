"""Placebo scoring: does an address's entry TIMING make money, or only its coins and direction?

Method is fixed in PREREGISTRATION.md. In short: every opening fill summed per (coin, hour)
is one decision; score = mean signed 24h forward log return from the close of that hour.
Placebo = the whole decision timeline circularly shifted by k hours inside its own span
(same coins, directions, count and spacing; only WHEN changes). p = share of shifts that
score >= the real timeline. Benjamini-Hochberg at q=0.10 across addresses.
"""
import json, io, os, sys, glob, hashlib, time
import numpy as np, pandas as pd
from scipy.stats import kstest, spearmanr

H = 3_600_000
OPEN = {"Open Long", "Open Short", "Long > Short", "Short > Long"}
HZ = 24          # forward horizon, hours
K = 1000         # placebo clones per address
MIN_DEC, MIN_SPAN = 50, 14 * 24
Q = 0.10


def decisions(fills):
    """[(coin, hour_ms, sign)] -- signed notional summed per (coin, hour); one decision each."""
    agg = {}
    for x in fills:
        if x.get("dir") not in OPEN:
            continue
        k = (x["coin"], int(x["time"]) // H * H)
        agg[k] = agg.get(k, 0.0) + (1 if x["side"] == "B" else -1) * float(x["px"]) * float(x["sz"])
    return [(c, h, 1 if v > 0 else -1) for (c, h), v in agg.items() if v != 0]


class Grid:
    """Hourly log closes on one global grid; R[t, c] = 24h forward log return from hour t."""
    def __init__(self, P):
        P = P.sort_index()
        full = np.arange(P.index.min(), P.index.max() + H, H)
        self.t0 = int(full[0])
        lp = np.log(P.reindex(full).to_numpy(dtype=float))
        self.R = np.full_like(lp, np.nan)
        self.R[:-HZ] = lp[HZ:] - lp[:-HZ]
        self.col = {c: i for i, c in enumerate(P.columns)}

    def idx(self, dec):
        d = [(self.col[c], (h - self.t0) // H, s) for c, h, s in dec if c in self.col]
        if not d:
            return None
        c, t, s = (np.array(v) for v in zip(*d))
        ok = (t >= 0) & (t < len(self.R))
        return c[ok], t[ok], s[ok]


def test(grid, dec, seed, shift_real=False):
    """Returns dict with real/direction/timing (bp per decision), p, n, span; None if ineligible."""
    v = grid.idx(dec)
    if v is None:
        return None
    c, t, s = v
    if not len(t):
        return None
    real_r = grid.R[t, c]
    n = int(np.isfinite(real_r).sum())
    lo, L = int(t.min()), int(t.max() - t.min() + 1)
    if n < MIN_DEC or L < MIN_SPAN:
        return None
    rng = np.random.default_rng(seed)
    if shift_real:   # calibration: a synthetic trader with no timing skill by construction
        t = lo + (t - lo + rng.integers(1, L)) % L
    real = np.nanmean(s * grid.R[t, c])
    ks = np.arange(1, L) if L - 1 <= K else rng.choice(np.arange(1, L), K, replace=False)
    tt = lo + ((t - lo)[None, :] + ks[:, None]) % L
    clones = np.nanmean(s[None, :] * grid.R[tt, c[None, :]], axis=1)
    clones = clones[np.isfinite(clones)]
    p = (1 + (clones >= real).sum()) / (1 + len(clones))
    return dict(n=n, span_days=round(L / 24, 1), real=1e4 * real, direction=1e4 * clones.mean(),
                timing=1e4 * (real - clones.mean()), p=float(p), clones=clones, ks=ks, t=t, c=c, s=s)


def bh(p, q=Q):
    p = np.asarray(p); m = len(p)
    o = np.argsort(p)
    ok = p[o] <= q * np.arange(1, m + 1) / m
    k = np.nonzero(ok)[0].max() + 1 if ok.any() else 0
    out = np.zeros(m, bool); out[o[:k]] = True
    return out


def seed_of(a, salt=""):
    return int(hashlib.sha256((a + salt).encode()).hexdigest()[:8], 16)


def run(grid, books, label=""):
    """books: {addr: decisions}. Returns DataFrame of eligible addresses (+ calibration)."""
    rows, cal = [], []
    for a, dec in books.items():
        r = test(grid, dec, seed_of(a))
        if r is None:
            continue
        z = test(grid, dec, seed_of(a, "cal"), shift_real=True)
        rows.append(dict(addr=a, **{k: r[k] for k in ("n", "span_days", "real", "direction", "timing", "p")}))
        cal.append(z["p"])
    d = pd.DataFrame(rows)
    if not len(d):
        print(f"{label}: no eligible addresses"); return d, None
    d["passes"] = bh(d.p.values)
    cp = np.array(cal)
    calib = dict(n=len(cp), pass_rate=float(bh(cp).mean()), raw05=float((cp < .05).mean()),
                 ks_p=float(kstest(cp, "uniform").pvalue))
    return d, calib


def summary(d, calib, label):
    print(f"\n== {label}: eligible {len(d)} ==")
    print(f"pass after BH q={Q}: {int(d.passes.sum())}   raw p<0.05: {int((d.p < .05).sum())} "
          f"({(d.p < .05).mean():.1%}, chance 5%)   raw p<0.01: {int((d.p < .01).sum())}")
    print(f"median bp/decision  real {d.real.median():.1f}  direction {d.direction.median():.1f}  "
          f"timing {d.timing.median():.1f}   timing<0: {(d.timing < 0).mean():.1%}")
    print(f"calibration (synthetic no-skill traders): pass {calib['pass_rate']:.1%}  "
          f"raw p<.05 {calib['raw05']:.1%}  KS p={calib['ks_p']:.3f}")


def detail(r, n_curves=30, pts=120):
    """Page payload: real cumulative curve inside a cloud of clone curves + clone histogram."""
    o = np.argsort(r["t"], kind="stable")
    t, c, s = r["t"][o], r["c"][o], r["s"][o]
    ks = r["ks"][np.linspace(0, len(r["ks"]) - 1, min(n_curves, len(r["ks"]))).astype(int)]
    lo, L = int(t.min()), int(t.max() - t.min() + 1)
    def curve(tt):
        x = np.nan_to_num(s * GRID.R[tt, c]); cs = np.cumsum(x) * 1e4
        i = np.linspace(0, len(cs) - 1, min(pts, len(cs))).astype(int)
        return [round(float(v), 1) for v in cs[i]]
    hist, edges = np.histogram(r["clones"] * 1e4, bins=40)
    return dict(real_curve=curve(t), clone_curves=[curve(lo + (t - lo + k) % L) for k in ks],
                hist=hist.tolist(), edges=[round(float(e), 2) for e in edges])


GRID = None


def _demo():
    """Self-check: a planted timing edge must be found, a no-skill trader must not."""
    rng = np.random.default_rng(1)
    T = 24 * 120
    r = rng.normal(0, .01, (T, 1))
    jumps = np.sort(rng.choice(np.arange(100, T - 100), 60, replace=False))
    r[jumps] += .06                                          # coin jumps up at random hours
    P = pd.DataFrame(np.exp(np.cumsum(r, 0)), index=np.arange(T) * H, columns=["X"])
    g = Grid(P)
    skilled = [("X", int(k - 1) * H, 1) for k in jumps]      # buys the hour before each jump
    lucky = [("X", h * H, 1) for h in rng.integers(0, T - 100, 60)]
    a, b = test(g, skilled, 7), test(g, lucky, 7)
    assert a["p"] < 0.01 and a["timing"] > 100, a["p"]
    assert b["p"] > 0.01, b["p"]
    assert bh([0.001, 0.2, 0.5]).tolist() == [True, False, False]
    print("demo ok", round(a["p"], 4), round(b["p"], 3))


def export(allx, books, pop, calib, out="web/data", asof=None):
    """Write the lookup page's data: index.json + one detail file per address."""
    os.makedirs(f"{out}/a", exist_ok=True)
    for _, row in allx.iterrows():
        a = row.addr
        r = test(GRID, books[a], seed_of(a))
        json.dump(dict(addr=a, kind=row.kind, name=pop.get(a, {}).get("name"), n=int(row.n),
                       **{k: round(float(row[k]), 2) for k in ("span_days", "real", "direction", "timing")},
                       p=round(float(row.p), 4), passes=bool(row.passes), **detail(r)),
                  io.open(f"{out}/a/{a}.json", "w"))
    idx = [dict(addr=r.addr, kind=r.kind, name=pop.get(r.addr, {}).get("name"), n=int(r.n),
                timing=round(float(r.timing), 1), direction=round(float(r.direction), 1),
                p=round(float(r.p), 4), passes=bool(r.passes)) for r in allx.itertuples()]
    json.dump(dict(asof=asof or time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), q=Q, horizon_h=HZ,
                   clones=K, calibration=calib, scores=idx), io.open(f"{out}/index.json", "w"))
    print(f"wrote {out} ({len(idx)} addresses)")


def candles(coins, lo, hi):
    """Hourly closes per coin, cached in data/px. Public candleSnapshot, throttled."""
    import pull
    os.makedirs("data/px", exist_ok=True)
    px = {}
    for i, cn in enumerate(sorted(coins)):
        f = f"data/px/{cn.replace(':', '_').replace('/', '_')}.json"
        if os.path.exists(f):
            k = json.load(io.open(f))
        else:
            try:
                k = pull.post({"type": "candleSnapshot", "req": {"coin": cn, "interval": "1h",
                               "startTime": lo - 2 * H, "endTime": hi + 30 * H}}, weight=20 + 40)
            except Exception:
                k = []
            if k:   # never cache a failure as an empty series
                json.dump(k, io.open(f, "w"))
        if i % 25 == 0:
            print(f"  px {i+1}/{len(coins)} {cn} n={len(k)}", flush=True)
        if len(k) > 50:
            px[cn] = pd.Series({int(b["t"]): float(b["c"]) for b in k})
    return pd.DataFrame(px)


def exposure(addr):
    """Current net/gross notional from clearinghouseState (H-C)."""
    try:
        st = json.load(io.open(f"data/states/{addr}.json"))
    except Exception:
        return None
    net = gross = 0.0
    for ap in st.get("assetPositions", []):
        q = ap["position"]; v = float(q["positionValue"])
        net += v if float(q["szi"]) > 0 else -v; gross += v
    return net / gross if gross else None


if __name__ == "__main__":
    _demo()
    if "--fresh" in sys.argv:
        pop = {p["addr"]: p for p in json.load(io.open("data/population.json", encoding="utf-8"))}
        books = {}
        for f in glob.glob("data/fills/*.json"):
            a = os.path.basename(f)[:-5]
            if a in pop:
                books[a] = decisions(json.load(io.open(f)))
        hrs = [h for b in books.values() for _, h, _ in b]
        coins = {c for b in books.values() for c, _, _ in b}
        print(f"{len(books)} addresses with fills, {len(coins)} coins", flush=True)
        GRID = Grid(candles(coins, min(hrs), max(hrs)))
        out = {}
        for kind in ("account", "vault"):
            sub = {a: b for a, b in books.items() if pop[a]["kind"] == kind}
            d, cal = run(GRID, sub)
            if not len(d):
                continue
            summary(d, cal, f"fresh {kind}s (top {'500 by 30d PnL' if kind == 'account' else '100 by TVL'})")
            d["kind"] = kind
            out[kind] = (d, cal)
        allx = pd.concat([v[0] for v in out.values()])
        acc = allx[allx.kind == "account"].copy()
        acc["roi"] = acc.addr.map(lambda a: pop[a]["month_roi"])
        acc["expo"] = acc.addr.map(exposure)
        m = acc.dropna(subset=["expo"])
        rho, pv = spearmanr(m.roi, m.expo)
        print(f"\nH-C: 30d ROI rank vs current net exposure (eligible accounts) rho={rho:.3f} p={pv:.2g} n={len(m)}")
        export(allx, books, pop, {k: v[1] for k, v in out.items()})
