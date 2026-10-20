#!/usr/bin/env python
"""单个 Gemini 生图任务的完整驱动（配合 gemini-image-gen skill）。

用法:
    python runtask.py <任务文件夹> <输出图片路径> [额外参考图路径 ...]

流程:
    1. 从任务文件夹的 `提示词.md` 中提取 "## Gemini 生图提示词" 之后的内容作为提示词
    2. 新建对话（navigate 到 gemini.google.com/app）
    3. 依次把参考图放进 Windows 剪贴板（ctypes CF_HDROP），聚焦输入框 Ctrl+V 粘贴
    4. 注入提示词 → 点击发送
    5. 轮询等待生成完成（model-response 内出现图片且无 spinner）
    6. 记录 Downloads 基线 → 点击 "Download full-sized image"
    7. 轮询检测新增图片文件 → 校验尺寸 → 复制到输出路径
    8. 打印 JSON 结果

环境变量: BSK_SESSION 指定会话 id（默认 ezni）
"""
import ctypes
import json
import os
import re
import struct
import subprocess
import sys
import time
import shutil
from ctypes import wintypes

SESSION = os.environ.get("BSK_SESSION", "ezni")
DOWNLOADS = r"C:/Users/shizh/Downloads"
TMP_DIR = r"C:/Users/shizh/WorkBuddy/2026-09-20-09-32-33"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
GMEM_MOVEABLE = 0x0002
CF_HDROP = 15

# 64 位下必须显式声明签名，否则句柄会被截断
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.CloseClipboard.restype = wintypes.BOOL


class DROPFILES(ctypes.Structure):
    _fields_ = [("pFiles", wintypes.DWORD), ("pt_x", wintypes.LONG), ("pt_y", wintypes.LONG),
                ("fNC", wintypes.BOOL), ("fWide", wintypes.BOOL)]


def log(*a):
    print(*a, flush=True)


def run_bsk(args, timeout=240):
    p = subprocess.run(["bsk"] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout or "") + (p.stderr or "")


def bsk_observe(max_tokens=3000):
    return run_bsk(["observe", "--session", SESSION, "--max-tokens", str(max_tokens)])


def find_ref(text, *label_subs):
    for line in text.splitlines():
        m = re.search(r"(@e\d+)\s+\w+(?:\s+\"([^\"]*)\")?", line)
        if m:
            label = (m.group(2) or "")
            for sub in label_subs:
                if sub.lower() in label.lower():
                    return m.group(1)
    return None


COMPOSER_LABELS = ["Enter a prompt for Gemini", "为 Gemini 输入提示"]
SEND_LABELS = ["Send message", "发送"]
NEWCHAT_LABELS = ["New chat", "发起新对话"]


def bsk_eval(js, timeout=180):
    return run_bsk(["evaluate", "--session", SESSION, "--timeout", "60s", js], timeout=timeout)


def set_clipboard_files(paths):
    files = "\0".join(paths) + "\0\0"
    df = DROPFILES()
    df.pFiles = ctypes.sizeof(DROPFILES)
    df.fWide = True
    data = bytes(df) + files.encode("utf-16-le")
    hglobal = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    ptr = kernel32.GlobalLock(hglobal)
    ctypes.memmove(ptr, data, len(data))
    kernel32.GlobalUnlock(hglobal)
    opened = False
    for _ in range(10):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.5)
    if not opened:
        raise RuntimeError("clipboard busy: OpenClipboard failed")
    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_HDROP, hglobal):
            raise RuntimeError("SetClipboardData failed")
    finally:
        user32.CloseClipboard()
    return True


def focus_composer():
    js = ("(function(){const el=document.querySelector('rich-textarea div[contenteditable=\"true\"]');"
          "if(!el) return JSON.stringify({ok:false});el.focus();el.click();return JSON.stringify({ok:true});})()")
    return bsk_eval(js)


UPLOAD_STATE_JS = """(function(){
  const blobs = [...document.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:'));
  let cont = null;
  if (blobs.length) {
    let el = blobs[0];
    for (let i = 0; i < 8 && el.parentElement; i++) {
      el = el.parentElement;
      if (el.querySelectorAll('img[src^="blob:"]').length >= blobs.length &&
          el.querySelectorAll('mat-progress-spinner,[role=progressbar]').length > 0) { cont = el; break; }
    }
  }
  const sendBtn = [...document.querySelectorAll('button')].find(b => /Send message|发送/.test(b.getAttribute('aria-label')||''));
  return JSON.stringify({
    blobs: blobs.length,
    spinInAttachmentArea: cont ? cont.querySelectorAll('mat-progress-spinner,[role=progressbar]').length : 0,
    sendLabel: sendBtn ? sendBtn.getAttribute('aria-label') : null,
    sendDisabled: sendBtn ? (sendBtn.getAttribute('aria-disabled') || String(sendBtn.disabled)) : null
  });
})()"""


def upload_state():
    out = bsk_eval(UPLOAD_STATE_JS)
    m = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {}


def wait_upload_done(prev_blobs, timeout=300):
    """等待"已新增附件且附件区不再有上传 spinner"。

    缩略图会立刻出现，但后台上传还要 20-30 秒/张；spinner 消失才代表上传完成。
    """
    t0 = time.time()
    stable = 0
    last = None
    while time.time() - t0 < timeout:
        st = upload_state()
        blobs = st.get("blobs", 0)
        spin = st.get("spinInAttachmentArea", 99)
        done = blobs > prev_blobs and spin == 0
        if done:
            stable += 1
            if stable >= 2:          # 连续两次采到完成态才算稳定
                return {"ok": True, "blobs": blobs, "waited": round(time.time() - t0, 1)}
        else:
            stable = 0
        last = st
        time.sleep(3)
    return {"ok": False, "reason": "upload timeout", "last": last, "waited": round(time.time() - t0, 1)}


def attachment_count():
    out = bsk_eval(UPLOAD_STATE_JS)
    m = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {}


def paste_file(path):
    set_clipboard_files([path])
    focus_composer()
    time.sleep(0.6)
    ref = find_ref(bsk_observe(1500), *COMPOSER_LABELS) or "@e5"
    res = run_bsk(["press", "Ctrl+V", "--ref", ref, "--session", SESSION])
    return res


def extract_prompt(task_dir):
    p = os.path.join(task_dir, "提示词.md")
    txt = open(p, encoding="utf-8").read()
    idx = txt.find("## Gemini 生图提示词")
    body = txt[idx + len("## Gemini 生图提示词"):] if idx >= 0 else txt
    return body.strip()


def new_chat():
    # 必须带 /u/1，否则会落到另一个（非会员）账号
    return run_bsk(["navigate", "https://gemini.google.com/u/1/app", "--session", SESSION])


def ensure_pro_mode():
    """新对话可能默认非 Pro 模式；确认并在需要时切回 Pro。"""
    time.sleep(3)
    txt = bsk_observe(1500)
    m = re.search(r"(@e\d+)\s+\w+\s+\"([^\"]*(?:mode picker|模式选择器)[^\"]*)\"", txt)
    if not m:
        log("  mode picker not found, skip check")
        return None
    label = m.group(2)
    if "Pro" in label:
        log("  mode: Pro ✓")
        return "Pro"
    log("  mode is NOT Pro:", label, "-> switching")
    run_bsk(["click", m.group(1), "--session", SESSION])
    time.sleep(1.5)
    txt2 = bsk_observe(2000)
    # 菜单项：Pro / Flash / Thinking 等，选择不含子菜单标记的 Pro 项
    m2 = re.search(r"(@e\d+)\s+\w+\s+\"Pro\"", txt2)
    if m2:
        run_bsk(["click", m2.group(1), "--session", SESSION])
        time.sleep(1.5)
        txt3 = bsk_observe(1500)
        m3 = re.search(r"(@e\d+)\s+\w+\s+\"([^\"]*(?:mode picker|模式选择器)[^\"]*)\"", txt3)
        log("  after switch:", m3.group(2) if m3 else "?")
        return m3.group(2) if m3 else None
    log("  Pro item not found in menu")
    return None


def send_prompt(prompt):
    js_ins = ("(function(){const el=document.querySelector('rich-textarea div[contenteditable=\"true\"]');"
              "if(!el) return JSON.stringify({ok:false,reason:'no editor'});el.focus();"
              "document.execCommand('insertText', false, " + json.dumps(prompt) + ");"
              "return JSON.stringify({ok:true,len:el.textContent.length});})()")
    r = bsk_eval(js_ins)
    log("  insert:", r.strip()[:120])
    time.sleep(1.2)

    # 关键：Gemini 的发送键在生成中会变成"停止生成"，误点会中断响应。
    # 因此只按"是否出现新响应 / 是否进入加载态"判断发送是否生效，
    # 绝不在加载中出现时再次点击。
    before = gen_state().get("responses", 0)
    for attempt in range(5):
        st = gen_state()
        if st.get("spinner", 0) > 0 or st.get("responses", 0) > before:
            if attempt:
                log("  sent on attempt %d" % (attempt + 1))
            return "sent"
        txt = bsk_observe(3000)
        ref = find_ref(txt, *SEND_LABELS)
        if not ref:
            log("  send button missing, wait...")
            time.sleep(5)
            continue
        run_bsk(["click", ref, "--session", SESSION])
        time.sleep(6)
    # 最后确认一次
    st = gen_state()
    if st.get("spinner", 0) > 0 or st.get("responses", 0) > before:
        return "sent"
    raise RuntimeError("send button not effective after retries")


def wait_idle(max_wait=180):
    """等待页面没有任何正在进行的生成，避免导航/新建对话中断进行中的响应。"""
    t0 = time.time()
    while time.time() - t0 < max_wait:
        st = gen_state()
        if st.get("spinner", 0) == 0:
            return True
        log("  page busy, waiting %ds" % (time.time() - t0))
        time.sleep(6)
    return False


def gen_state():
    js = ("(function(){const r=Array.from(document.querySelectorAll('model-response'));"
          "const l=r[r.length-1];const t=l?(l.innerText||'').trim():'';"
          "return JSON.stringify({responses:r.length,lastImgs:l?l.querySelectorAll('img').length:-1,"
          "spinner:document.querySelectorAll('loading-indicator, .loading-spinner').length,"
          "prog:document.querySelectorAll('mat-progress-spinner,[role=progressbar]').length,"
          "creating:/正在创建您的图片|Creating your image|正在生成图片/i.test(t),"
          "refused:/没办法提供|无法提供|不能提供|我没办法|I can.t help|unable to provide|can.t generate|I.m unable/i.test(t),"
          "textLen:t.length,sent:!!document.querySelector('user-query')});})()")
    # 注意：正则里不要出现字面单引号（会让 bsk evaluate 传参失败返回空），用 . 通配
    out = bsk_eval(js)
    m = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {}


def diagnose_response():
    """生成超时/无图时抓取最后一条响应的实际内容，用于判断是拒绝、报错还是纯文本回复。"""
    js = ("(function(){const r=Array.from(document.querySelectorAll('model-response'));"
          "if(!r.length) return JSON.stringify({responses:0});"
          "const l=r[r.length-1];const t=(l.innerText||'').trim();"
          "const q=document.querySelectorAll('user-query').length;"
          "return JSON.stringify({responses:r.length,queries:q,len:t.length,head:t.slice(0,400)});})()")
    out = bsk_eval(js)
    m = re.search(r"\{.*\}", out, re.S)
    try:
        return json.loads(m.group(0)) if m else {"raw": out[:400]}
    except Exception:
        return {"raw": out[:400]}


def wait_generated(timeout=1200):
    """等待生成完成。返回 {"ok":bool, "refused":bool, "state":..., "text":...}。

    关键教训：
    1. **不要用 spinner 判完成**。Gemini 出图前的长时间里显示「正在创建您的图片 /
       Creating your image」，此时 `loading-indicator / .loading-spinner` 计数为 0，
       用 "spinner==0" 当结束条件会误判成"已完成但没图"并提前放弃。
       唯一可靠的完成判据：最后一条 model-response 内出现 img。
    2. **被安全过滤拒绝时不要干等到超时**。模型会回「身为一个语言模型，我没办法提供
       这方面的帮助。」——识别到就立刻返回 refused，让上层重试或改写提示词。
    """
    t0 = time.time()
    time.sleep(15)
    while time.time() - t0 < timeout:
        st = gen_state()
        if st.get("lastImgs", 0) >= 1:
            log("  generated:", st, "%.0fs" % (time.time() - t0))
            return {"ok": True, "state": st, "waited": round(time.time() - t0, 1)}
        if st.get("refused"):
            text = diagnose_response().get("head", "")
            log("  REFUSED by safety filter:", text[:120])
            return {"ok": False, "refused": True, "state": st, "text": text,
                    "waited": round(time.time() - t0, 1)}
        tag = "creating-image" if st.get("creating") else "waiting"
        log("  %s:" % tag, st, "%.0fs" % (time.time() - t0))
        time.sleep(10)
    return {"ok": False, "refused": False, "state": gen_state(),
            "text": diagnose_response().get("head", ""), "waited": round(time.time() - t0, 1)}


def baseline_downloads():
    return set(os.listdir(DOWNLOADS))


def trigger_download():
    js = ("(function(){const r=Array.from(document.querySelectorAll('model-response'));"
          "const l=r[r.length-1];if(!l) return JSON.stringify({ok:false,reason:'no response'});"
          "const b=Array.from(l.querySelectorAll('button')).filter(x=>{const a=x.getAttribute('aria-label')||'';"
          "return a.includes('Download')||a.includes('下载')});"
          "if(!b.length) return JSON.stringify({ok:false,reason:'no download btn'});"
          "b[b.length-1].click();return JSON.stringify({ok:true});})()")
    return bsk_eval(js)


def jpg_size(path):
    with open(path, "rb") as fp:
        d = fp.read()
    i = 2
    while i < len(d) - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return w, h
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return None


def wait_download(before, out_path, timeout=90):
    IMG = (".jpg", ".jpeg", ".png", ".webp")
    t0 = time.time()
    while time.time() - t0 < timeout:
        added = [f for f in set(os.listdir(DOWNLOADS)) - before if f.lower().endswith(IMG)]
        for name in added:
            p = os.path.join(DOWNLOADS, name)
            try:
                s1 = os.path.getsize(p)
            except OSError:
                continue
            time.sleep(2)
            try:
                s2 = os.path.getsize(p)
            except OSError:
                continue
            if s1 != s2 or s1 < 100 * 1024:
                continue
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            shutil.copy2(p, out_path)
            size = jpg_size(p) or (0, 0)
            return {"ok": True, "source": p, "copied_to": out_path, "bytes": s2,
                    "dimensions": "%dx%d" % size}
        time.sleep(3)
    return {"ok": False, "reason": "download timeout"}


def main():
    task_dir = sys.argv[1]
    out_path = sys.argv[2]
    extra_refs = sys.argv[3:]

    ref_dir = os.path.join(task_dir, "参考图")
    refs = []
    if os.path.isdir(ref_dir):
        refs = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    refs += extra_refs
    refs = [r.replace("\\", "/") for r in refs]

    result = {"task": os.path.basename(task_dir), "output": out_path}
    log("[1/7] 新建对话")
    new_chat()
    time.sleep(4)
    mode = ensure_pro_mode()
    result["mode"] = mode

    log("[2/7] 上传参考图 (%d 张)" % len(refs))
    for r in refs:
        paste_file(r)
        time.sleep(5)
        log("      pasted:", os.path.basename(r), attachment_count())

    prompt = extract_prompt(task_dir)
    log("[3/7] 发送提示词 (%d 字)" % len(prompt))
    send_prompt(prompt)

    log("[4/7] 等待生成")
    gen = wait_generated()
    if not gen.get("ok"):
        result["error"] = "model refused (safety filter)" if gen.get("refused") else "generation timeout"
        result["diag"] = gen.get("text", "")[:300]
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    log("[5/7] 记录下载基线")
    before = baseline_downloads()

    log("[6/7] 触发下载")
    trigger_download()

    log("[7/7] 等待落盘并复制")
    dl = wait_download(before, out_path)
    result.update(dl)
    print(json.dumps(result, ensure_ascii=False))
    if not dl.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
