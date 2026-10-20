#!/usr/bin/env python
"""收割当前页面上正在进行的生成：等出图 → 下载 → 存到指定路径。"""
import os
import sys

os.environ.setdefault("BSK_SESSION", "qrfg")
import runtask as R

out = sys.argv[1]

st = R.gen_state()
print("start state:", st, flush=True)
if st.get("lastImgs", 0) < 1:
    print("waiting for image...", flush=True)
    res = R.wait_generated(1200)
    if not res.get("ok"):
        print("FAILED refused=%s diag=%s" % (res.get("refused"), str(res.get("text", ""))[:200]), flush=True)
        sys.exit(1)

before = R.baseline_downloads()
R.trigger_download()
dl = R.wait_download(before, out, 120)
print("result:", dl, flush=True)
sys.exit(0 if dl.get("ok") else 1)
