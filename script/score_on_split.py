#!/usr/bin/env python3
"""Score an official eval result on a subset of instance ids (a data split).

Usage:
    score_on_split.py <eval_official_results.json> --all
    score_on_split.py <eval_official_results.json> <ids_file.txt>

Prints one compact cell: "45.0% (180/400)"  (instance/hard accuracy on the split).
Instance accuracy = fully-correct instances / instances-present-in-this-split.
"""
import json
import sys


def main():
    if len(sys.argv) < 3:
        print("n/a"); return
    eval_json, which = sys.argv[1], sys.argv[2]
    try:
        data = json.load(open(eval_json, encoding="utf-8"))
    except Exception:
        print("n/a"); return
    results = data.get("results", data if isinstance(data, list) else [])

    if which == "--all":
        subset = results
    else:
        try:
            ids = {ln.strip() for ln in open(which, encoding="utf-8") if ln.strip()}
        except Exception:
            print("n/a"); return
        subset = [r for r in results if str(r.get("id")) in ids]

    n = len(subset)
    if n == 0:
        print("0/0"); return
    correct = sum(1 for r in subset if r.get("success"))
    print(f"{correct / n * 100:.1f}% ({correct}/{n})")


if __name__ == "__main__":
    main()
