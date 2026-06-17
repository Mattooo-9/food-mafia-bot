#!/usr/bin/env python3
"""Render service status helper (reads RENDER_API_KEY from env)."""
import json
import os
import sys
import urllib.request

SID = os.environ.get("RENDER_SERVICE_ID", "srv-d8a9cmq8qa3s73elgkc0")


def api(path: str) -> dict:
    key = os.environ["RENDER_API_KEY"]
    req = urllib.request.Request(
        f"https://api.render.com/v1{path}",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main() -> None:
    svc = api(f"/services/{SID}")
    details = svc.get("serviceDetails", {})
    print("runtime:", details.get("runtime"))
    print("url:", details.get("url"))
    print("envSpecific:", json.dumps(details.get("envSpecificDetails"), ensure_ascii=False))
    deploys = api(f"/services/{SID}/deploys?limit=3")
    for item in deploys:
        d = item.get("deploy", item)
        print("deploy:", d.get("status"), d.get("finishedAt"), d.get("commit", {}).get("message", "")[:60])


if __name__ == "__main__":
    main()
