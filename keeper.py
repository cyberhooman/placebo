"""Push web/data/index.json scores to PlaceboRegistry on HyperEVM (batches of 50: ~1.5M gas,
under the 3M small-block limit). Needs Foundry's `cast` and .env with PLACEBO_DEPLOYER_KEY.

  python keeper.py <registry address> [--rpc URL]
"""
import json, io, os, subprocess, sys, calendar, time

RPC = "https://rpc.hyperliquid-testnet.xyz/evm"
SIG = "push(address[],(uint32,int32,int32,int32,uint16,bool,uint64)[])"
BATCH = 50


def env():
    e = {}
    for line in io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def tuples(rows, as_of):
    return "[" + ",".join(
        f"({r['n']},{round(r['real'])},{round(r['direction'])},{round(r['timing'])},"
        f"{min(10000, round(r['p'] * 10000))},{str(r['passes']).lower()},{as_of})" for r in rows) + "]"


if __name__ == "__main__":
    reg = sys.argv[1]
    rpc = sys.argv[sys.argv.index("--rpc") + 1] if "--rpc" in sys.argv else RPC
    ix = json.load(io.open("web/data/index.json"))
    # index.json keeps timing/direction; real = direction + timing
    rows = [dict(s, real=s["direction"] + s["timing"]) for s in ix["scores"]]
    try:
        as_of = calendar.timegm(time.strptime(ix["asof"][:16], "%Y-%m-%d %H:%M"))
    except ValueError:
        as_of = calendar.timegm(time.strptime(ix["asof"][:10], "%Y-%m-%d"))
    key = env()["PLACEBO_DEPLOYER_KEY"]
    for i in range(0, len(rows), BATCH):
        b = rows[i:i + BATCH]
        addrs = "[" + ",".join(r["addr"] for r in b) + "]"
        out = subprocess.run(["cast", "send", reg, SIG, addrs, tuples(b, as_of), "--rpc-url", rpc,
                              "--private-key", key, "--json"], capture_output=True, text=True)
        if out.returncode:
            sys.exit(f"batch {i // BATCH} failed: {out.stderr[-400:]}")
        tx = json.loads(out.stdout)
        print(f"batch {i // BATCH}: {len(b)} scores, gas {int(tx['gasUsed'], 16)}, tx {tx['transactionHash']}", flush=True)
    for fn in ("scored()(uint32)", "passed()(uint32)"):
        print(fn, subprocess.run(["cast", "call", reg, fn, "--rpc-url", rpc], capture_output=True, text=True).stdout.strip())
