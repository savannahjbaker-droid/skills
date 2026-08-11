#!/usr/bin/env python3
"""
Check provider network status through InNetwork.ai (Credflow) — in bulk.

WHAT IT DOES
  Reads a CSV of providers + payers, asks InNetwork.ai whether each provider is
  in-network with each payer, and writes the answers to a results CSV you can
  paste into your tracker.

WHY A SCRIPT
  Your credentials and the internet connection live on YOUR computer. This runs
  there and talks to InNetwork.ai directly. (It uses only Python's standard
  library — nothing to install.)

--------------------------------------------------------------------------------
SETUP (one time)
  1. Install Python 3 if you don't have it:  https://www.python.org/downloads/
  2. Put your API key in an environment variable (NEVER hard-code it here).
     Start with a SANDBOX key while testing — it returns synthetic data, free.

     macOS / Linux:
         export INNETWORK_API_KEY="sk_test_xxxxxxxx"
     Windows (PowerShell):
         $env:INNETWORK_API_KEY="sk_test_xxxxxxxx"

RUN
     python innetwork_check.py providers.csv results.csv

INPUT FILE  (providers.csv) — a header row then one row per check:
     npi,payer
     1234567893,aetna
     1234567893,cigna
     1987654320,uhc

OUTPUT FILE (results.csv):
     npi,payer,in_network,raw_status,ok,message
--------------------------------------------------------------------------------

If you ever get a 401 Unauthorized: your key header may differ. See AUTH below.
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("INNETWORK_BASE_URL", "https://innetwork-be.credflow.ai/v1")
API_KEY = os.environ.get("INNETWORK_API_KEY")


def auth_headers():
    # AUTH: InNetwork.ai uses a bearer token. If you get 401, check the docs'
    # "Authorize" section — some APIs use {"x-api-key": API_KEY} instead. Swap
    # the line below if so.
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def check(npi: str, payer: str) -> dict:
    """Call POST /v1/providers/status for one provider + payer."""
    body = json.dumps({"npi": npi, "payer": payer}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/providers/status", data=body, headers=auth_headers(), method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": "", "message": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "", "message": f"{type(e).__name__}: {e}"}

    data = payload.get("data") or {}
    return {
        "ok": bool(payload.get("success")),
        "status": data.get("status", ""),
        "message": payload.get("message", ""),
    }


IN_NETWORK = {"active", "in_network", "in-network", "enrolled", "participating"}


def main() -> int:
    if not API_KEY:
        print("ERROR: set INNETWORK_API_KEY first (see SETUP at the top).")
        return 1
    if len(sys.argv) < 2:
        print("Usage: python innetwork_check.py providers.csv [results.csv]")
        return 1

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "results.csv"

    with open(in_path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("npi") and r.get("payer")]

    print(f"Checking {len(rows)} provider/payer pair(s) via {BASE_URL} ...\n")
    results = []
    for i, r in enumerate(rows, 1):
        npi, payer = r["npi"].strip(), r["payer"].strip().lower()
        res = check(npi, payer)
        in_net = "YES" if res["status"].lower() in IN_NETWORK else "no"
        results.append({
            "npi": npi, "payer": payer, "in_network": in_net,
            "raw_status": res["status"], "ok": res["ok"], "message": res["message"],
        })
        flag = "✓ in-network" if in_net == "YES" else f"· {res['status'] or res['message']}"
        print(f"  [{i}/{len(rows)}] {npi}  {payer:12} {flag}")
        time.sleep(0.25)  # be gentle on the API

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["npi", "payer", "in_network", "raw_status", "ok", "message"])
        w.writeheader()
        w.writerows(results)

    in_count = sum(1 for r in results if r["in_network"] == "YES")
    print(f"\nDone. {in_count}/{len(results)} in-network. Results written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
