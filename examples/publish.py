#!/usr/bin/env python3
"""Upload a dump to Zdex.

    python publish.py game.json "Game title" "1.4.2"

Put your API key in ZDEX_API_KEY (account page -> API keys).
Protocol: https://zlogic.eu/zdex/developers
"""
import gzip
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("ZDEX_URL", "https://zlogic.eu/zdex").rstrip("/") + "/api/v1"
KEY = os.environ.get("ZDEX_API_KEY", "")
UA = "zdex-publish-example/1.0 (+https://github.com/TheHolyOneZ/Zdex)"


def call(method, path, body=None, raw=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("User-Agent", UA)
    if KEY:
        req.add_header("Authorization", "Bearer " + KEY)
    data = None
    if raw is not None:
        data = raw
        req.add_header("Content-Type", "application/octet-stream")
    elif body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=300) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, {"ok": False, "error": "not_json", "message": text[:200]}


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    if not KEY:
        sys.exit("set ZDEX_API_KEY first")
    src, game, label = sys.argv[1:4]
    data = open(src, "rb").read()
    name = os.path.basename(src)
    if not name.endswith((".gz", ".zip")):
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as g:
            g.write(data)
        data, name = buf.getvalue(), name + ".gz"

    st, r = call("POST", "/upload/init", {"filename": name, "size": len(data), "game": game, "label": label})
    if not r.get("ok"):
        sys.exit("init failed: %s (%s)" % (r.get("message"), r.get("error")))
    uid, chunk, count = r["upload_id"], r["chunk_bytes"], r["chunk_count"]
    for i in range(count):
        st, rr = call("POST", "/upload/chunk?upload_id=%s&index=%d" % (uid, i), raw=data[i * chunk:(i + 1) * chunk])
        if st != 200:
            sys.exit("chunk %d failed: %s" % (i, rr.get("message")))
        print("chunk %d/%d" % (i + 1, count))

    st, r = call("POST", "/upload/finish", {"upload_id": uid})
    if r.get("duplicate"):
        print("already on Zdex:", r.get("url"))
        return
    if not r.get("ok"):
        sys.exit("finish failed: %s (%s)" % (r.get("message"), r.get("error")))
    dump_id, url = r["dump_id"], r["url"]
    for _ in range(200):
        st, s = call("GET", "/dump/%d/status" % dump_id)
        print("status:", s.get("status"), s.get("progress"), s.get("phase_label") or "")
        if s.get("status") in ("ready", "pending", "failed"):
            break
        time.sleep(3)
    print(url)


if __name__ == "__main__":
    main()
