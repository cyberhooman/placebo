"""Amendment 1, A2: were the top-500 accounts' entries well timed BEFORE the 30-day window that
put them on the leaderboard? Same placebo test, decisions split at 2026-09-05 08:00 UTC."""
import json, io, glob, os, calendar, time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import score

CUT = calendar.timegm(time.strptime("2026-09-05 08:00", "%Y-%m-%d %H:%M")) * 1000
pop = {p["addr"]: p for p in json.load(io.open("data/population.json", encoding="utf-8"))}
books = {os.path.basename(f)[:-5]: score.decisions(json.load(io.open(f))) for f in glob.glob("data/fills/*.json")}
books = {a: b for a, b in books.items() if pop[a]["kind"] == "account"}
coins = {c for b in books.values() for c, _, _ in b}
hrs = [h for b in books.values() for _, h, _ in b]
score.GRID = grid = score.Grid(score.candles(coins, min(hrs), max(hrs)))
res = {}
for part, keep in (("pre", lambda h: h < CUT), ("in", lambda h: h >= CUT)):
    sub = {a: [d for d in b if keep(d[1])] for a, b in books.items()}
    d, cal = score.run(grid, sub, min_dec=30, min_span=7 * 24)
    score.summary(d, cal, f"top-500 accounts, {part}-window decisions")
    res[part] = d.set_index("addr")
both = res["pre"].join(res["in"], lsuffix="_pre", rsuffix="_in", how="inner")
rho, p = spearmanr(both.timing_pre, both.timing_in)
print(f"\neligible in both: {len(both)}   Spearman timing pre vs in: rho={rho:.3f} p={p:.2g}")
print(f"of those: pre timing>0 {(both.timing_pre > 0).mean():.1%}, in timing>0 {(both.timing_in > 0).mean():.1%}")
pd.concat({k: v for k, v in res.items()}).to_csv("data/oos_split.csv")
