"""Run the pre-registered test on the 8 Sep 2026 archive sample (600 accounts, volume-stratified)."""
import json, io, glob, os, time
import pandas as pd
import score

A = "D:/code/Crypto experiments archive/data"
t0 = time.time()
score.GRID = grid = score.Grid(pd.read_parquet(f"{A}/prices.parquet"))
books = {os.path.basename(p)[:-5]: score.decisions(json.load(io.open(p, encoding="utf-8")))
         for p in glob.glob(f"{A}/fills/*.json")}
d, cal = score.run(grid, books)
score.summary(d, cal, "8 Sep 2026 sample (600 accounts, 10 volume deciles)")
d.to_csv("data/sep8_scores.csv", index=False)
d["kind"] = "account"
if "--export" in __import__("sys").argv:   # sample data for building the page; overwritten by the fresh run
    score.export(d, books, {}, {"account": cal}, out="web/data", asof="2026-09-08 (archive sample)")
print(f"{time.time()-t0:.0f}s")
