"""Fetch hourly candles for every coin seen in data/fills while pull.py runs, using the
~13% of the rate budget pull.py leaves free (one call per 25 s). Same cache as score.candles."""
import json, io, os, glob, time, requests
import score

H, DAY = 3_600_000, 86_400_000
os.makedirs("data/px", exist_ok=True)
while True:
    coins = set()
    for f in glob.glob("data/fills/*.json"):
        try:
            coins |= {c for c, _, _ in score.decisions(json.load(io.open(f)))}
        except Exception:
            pass
    todo = [c for c in sorted(coins) if not os.path.exists(f"data/px/{c.replace(':', '_').replace('/', '_')}.json")]
    done = "DONE" in io.open("data/pull.log").read()
    print(f"{time.strftime('%H:%M')} coins {len(coins)} missing {len(todo)} pull_done={done}", flush=True)
    if not todo and done:
        break
    now = int(time.time() * 1000)
    for c in todo[:20]:
        try:
            r = requests.post("https://api.hyperliquid.xyz/info", json={"type": "candleSnapshot", "req": {
                "coin": c, "interval": "1h", "startTime": now - 93 * DAY, "endTime": now + H}}, timeout=30)
            k = r.json() if r.status_code == 200 else []
        except Exception:
            k = []
        if k:
            json.dump(k, io.open(f"data/px/{c.replace(':', '_').replace('/', '_')}.json", "w"))
        time.sleep(25)
    if not todo:
        time.sleep(120)
