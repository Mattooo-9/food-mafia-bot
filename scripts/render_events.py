#!/usr/bin/env python3
import json
import os
import urllib.request

SID = os.environ.get("RENDER_SERVICE_ID", "srv-d8a9cmq8qa3s73elgkc0")
key = os.environ["RENDER_API_KEY"]

for path in [f"/services/{SID}/events?limit=10", f"/services/{SID}/deploys?limit=1"]:
    req = urllib.request.Request(
        f"https://api.render.com/v1{path}",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    print("===", path)
    print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
