"""Pull the population: top 500 leaderboard accounts by 30-day PnL (>= $1M 30-day volume) + top 100 open vaults by TVL.

For each address: current positions (clearinghouseState) and the last 90 days of fills.
Resume-safe: anything already on disk is skipped. Public read-only endpoints only.
"""
import json, io, os, sys, time
import requests

U = "https://api.hyperliquid.xyz/info"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DAY = 86_400_000
_last = [0.0]


def post(body, weight=20, tries=6):
    # HL budget is 1200 weight/min/IP = 20/s. Sleep for the call we're about to make.
    for i in range(tries):
        wait = weight / 20 * 1.15 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.post(U, json=body, timeout=30)
            if r.status_code == 200:
                return r.json()
            time.sleep((20 if r.status_code == 429 else 3) * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"failed: {str(body)[:120]}")


def population(n_acc=500, n_vault=100):
    rows = json.load(io.open(f"{D}/leaderboard.json", encoding="utf-8"))["leaderboardRows"]
    acc = []
    for x in rows:
        w = {k: v for k, v in x["windowPerformances"]}
        acc.append(dict(addr=x["ethAddress"].lower(), kind="account", name=x.get("displayName"),
                        av=float(x["accountValue"]),
                        **{f"{k}_{f}": float(w[k][f]) for k in w for f in ("pnl", "vlm", "roi")}))
    # traders only: the top raw PnL rows include zero-volume holders (e.g. a $3.3B account, 0 volume)
    acc = [r for r in acc if r["month_vlm"] >= 1e6]
    acc.sort(key=lambda r: -r["month_pnl"])
    vaults = [v["summary"] for v in json.load(io.open(f"{D}/vaults.json", encoding="utf-8"))]
    vaults = [v for v in vaults if not v["isClosed"] and float(v["tvl"]) > 0]
    vaults.sort(key=lambda v: -float(v["tvl"]))
    va = [dict(addr=v["vaultAddress"].lower(), kind="vault", name=v["name"], tvl=float(v["tvl"]),
               leader=v["leader"]) for v in vaults[:n_vault]]
    seen, out = set(), []
    for r in acc[:n_acc] + va:
        if r["addr"] not in seen:
            seen.add(r["addr"]); out.append(r)
    return out


def fills(addr, days=90):
    """userFillsByTime pages ascending from startTime, 2000 per page; HL keeps only the
    10,000 most recent fills, so very active accounts come back shorter than 90 days."""
    now = int(time.time() * 1000)
    cur, out, seen = now - days * DAY, [], set()
    while cur < now:
        b = post({"type": "userFillsByTime", "user": addr, "startTime": cur,
                  "endTime": now, "aggregateByTime": True}, weight=20 + 100)
        new = [f for f in b if f["tid"] not in seen]
        if not new:
            break
        for f in new:
            seen.add(f["tid"])
        out += new
        if len(b) < 2000:
            break
        cur = max(int(f["time"]) for f in b)
    return out


if __name__ == "__main__":
    os.makedirs(f"{D}/fills", exist_ok=True)
    os.makedirs(f"{D}/states", exist_ok=True)
    pop = population()
    json.dump(pop, io.open(f"{D}/population.json", "w", encoding="utf-8"))
    print(f"population {len(pop)}: {sum(p['kind']=='account' for p in pop)} accounts, "
          f"{sum(p['kind']=='vault' for p in pop)} vaults", flush=True)
    t0 = time.time()
    for i, p in enumerate(pop):
        a = p["addr"]
        try:
            s = f"{D}/states/{a}.json"
            if not os.path.exists(s):
                json.dump(post({"type": "clearinghouseState", "user": a}, weight=2), io.open(s, "w"))
            f = f"{D}/fills/{a}.json"
            if not os.path.exists(f):
                fl = fills(a)
                json.dump(fl, io.open(f + ".tmp", "w"))
                os.replace(f + ".tmp", f)  # only complete pulls count as done
                n = len(fl)
            else:
                n = "cached"
        except Exception as e:
            n = f"ERR {e}"
        if i % 10 == 0 or i == len(pop) - 1:
            print(f"{i+1}/{len(pop)} {p['kind']:7s} {a[:10]} fills={n} {time.time()-t0:.0f}s", flush=True)
    print("DONE", flush=True)
