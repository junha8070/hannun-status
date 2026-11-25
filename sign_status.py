#!/usr/bin/env python3
"""
한눈 버전 상태 파일 서명 도구.

policy.json(사람이 고치는 파일)을 읽어 서명된 status.json을 만들어요.
앱은 status.json의 서명이 맞을 때만 믿어요. 비밀 키는 이 폴더 밖에 두세요.

사용법:
  python3 sign_status.py                       # 기본 키 위치 사용
  python3 sign_status.py --key /경로/status_private.pem

기본 키 위치: 이 폴더의 한 단계 위 '한눈-상태서명키(공유금지)/status_private.pem'
"""
import argparse, base64, json, os, re, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KEY = os.path.join(os.path.dirname(HERE), "한눈-상태서명키(공유금지)", "status_private.pem")
APP_ID = "com.xlntsmmr.invest"
VERSION_RE = re.compile(r"^\d{1,4}(\.\d{1,4}){0,3}$")
ALLOWED_URL_HOSTS = {"play.google.com", "github.com"}

# 앱에 박힌 공개 키와 같아야 해요 (다르면 앱이 무시)
APP_PUBLIC_KEY_B64 = "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEjyz2GhnItXm9z69R/Hh0Z3AQu7/5xNmuR2uZBhkJVs2EY5ufe7DZfAU35W7yRUokqePY3qt1bc05LKKpw4zMkg=="


def fail(msg):
    print("❌ " + msg); sys.exit(1)


def check_channel(name, ch):
    for v in [ch.get("minVersion", ""), ch.get("latest", "")] + list(ch.get("blocked", [])):
        if v and not VERSION_RE.match(v.strip()):
            fail(f"{name}: 버전 형식이 이상해요 → {v!r} (예: 1.0.0)")
    url = ch.get("url", "")
    if url:
        m = re.match(r"^https://([^/:@]+)(/|$)", url)
        if not m or m.group(1).lower() not in ALLOWED_URL_HOSTS:
            fail(f"{name}: url은 https://play.google.com 또는 https://github.com 주소만 돼요 → {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("HANNUN_STATUS_KEY", DEFAULT_KEY))
    a = ap.parse_args()
    key = os.path.abspath(a.key)
    if not os.path.isfile(key):
        fail(f"비밀 키를 찾을 수 없어요: {key}")
    if os.path.commonpath([key, HERE]) == HERE:
        fail("비밀 키가 저장소 폴더 안에 있어요. 밖으로 옮긴 뒤 다시 해 주세요 (깃허브에 올라가면 안 돼요).")

    with open(os.path.join(HERE, "policy.json"), encoding="utf-8") as f:
        policy = json.load(f)
    for ch in ("android", "desktop"):
        check_channel(ch, policy.get(ch, {}))
    if len(policy.get("message", "")) > 400 or len(policy.get("title", "")) > 60:
        fail("title은 60자, message는 400자까지예요")

    # 되돌리기 방지: issuedAt은 지난번보다 항상 커야 해요
    issued = int(time.time())
    try:
        with open(os.path.join(HERE, "status.json"), encoding="utf-8") as f:
            prev = json.loads(base64.b64decode(json.load(f)["payload"]))
            issued = max(issued, int(prev.get("issuedAt", 0)) + 1)
    except FileNotFoundError:
        pass

    payload = dict(policy, app=APP_ID, issuedAt=issued)
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    with tempfile.TemporaryDirectory() as td:
        pf = os.path.join(td, "payload"); sf = os.path.join(td, "sig"); pub = os.path.join(td, "pub.der")
        open(pf, "wb").write(payload_bytes)
        subprocess.run(["openssl", "dgst", "-sha256", "-sign", key, "-out", sf, pf], check=True)
        # 앱과 같은 공개 키로 검증까지 해 보고 저장
        open(pub, "wb").write(base64.b64decode(APP_PUBLIC_KEY_B64))
        pubpem = os.path.join(td, "pub.pem")
        subprocess.run(["openssl", "pkey", "-pubin", "-inform", "DER", "-in", pub, "-out", pubpem], check=True)
        r = subprocess.run(["openssl", "dgst", "-sha256", "-verify", pubpem, "-signature", sf, pf], capture_output=True, text=True)
        if "Verified OK" not in r.stdout:
            fail("이 키로 만든 서명이 앱의 공개 키와 맞지 않아요. 키 파일을 확인해 주세요.")
        sig = open(sf, "rb").read()

    out = {"v": 1, "payload": base64.b64encode(payload_bytes).decode(), "sig": base64.b64encode(sig).decode()}
    with open(os.path.join(HERE, "status.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":")); f.write("\n")
    print("✅ status.json을 만들었어요 (issuedAt=%d)" % issued)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\n이제 status.json을 깃허브 junha8070/hannun-status 저장소 main 브랜치에 올리면 돼요.")


if __name__ == "__main__":
    main()
