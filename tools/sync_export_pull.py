#!/usr/bin/env python3
"""Run on the office Mac: pull queued project documents and file them in the Sync folder (never overwrites).

usage: sync_export_pull.py --base https://<app> --token <EXPORT_TOKEN> --root "/Volumes/FP70/Sync/3. BRAYMAN CONSTRUCTION/01 - Projects"
"""
import argparse, hashlib, json, os, urllib.request

def call(url, token, data=None):
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    return urllib.request.urlopen(req, timeout=60).read()

def free_path(path):
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f"{stem}_v{n}{ext}"):
        n += 1
    return f"{stem}_v{n}{ext}"

def main():
    a = argparse.ArgumentParser(); a.add_argument("--base", required=True); a.add_argument("--token", required=True)
    a.add_argument("--root", required=True); args = a.parse_args()
    for item in json.loads(call(args.base + "/sync-export/pending", args.token)):
        try:
            data = call(f"{args.base}/sync-export/{item['id']}/file", args.token)
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("hash mismatch")
            folder = os.path.join(args.root, item["project_folder"], item["folder"])
            os.makedirs(folder, exist_ok=True)
            path = free_path(os.path.join(folder, item["target_name"]))
            with open(path, "xb") as fh:
                fh.write(data)
            body = json.dumps({"sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}).encode()
            call(f"{args.base}/sync-export/{item['id']}/done", args.token, body)
            print("filed", path)
        except Exception as exc:
            call(f"{args.base}/sync-export/{item['id']}/failed", args.token, json.dumps({"error": str(exc)}).encode())
            print("FAILED", item["target_name"], exc)

if __name__ == "__main__":
    main()
