<<<<<<< HEAD
import os
import time
import threading
import requests
# 맨 위 import 근처에 추가
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body

# (앱 생성 직후) CORS 허용 – https://snack.expo.dev, Expo Go 등에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 필요시 도메인 제한 가능
=======
import os, time, threading, requests
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ===== 환경 =====
BEARER = os.environ["X_BEARER_TOKEN"]  # X API Bearer
QUERY = os.environ.get("QUERY", '(솔음른 배포전 OR 솔음른배포전) -is:retweet lang:ko')
INTERVAL_SEC = int(os.environ.get("INTERVAL_SEC", "1800"))  # 30분
PORT = int(os.environ.get("PORT", "8080"))

# ===== 상태 =====
STATE: Dict[str, Any] = {"since_id": None, "last_run": None, "device_tokens": set()}

class RegisterPayload(BaseModel):
    token: str  # Expo push token (ExponentPushToken[...])

app = FastAPI()

# CORS (Snack/Expo Go 포함 폭넓게 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# pydantic 모델 그대로 두고, /register 와 /register-device 둘 다 허용
@app.post("/register")
@app.post("/register-device")
def register_device(p: RegisterPayload = Body(...)):
    token = p.token.strip()
    print(f"[REGISTER] {token}")          # 로그로 확인
    if "ExponentPushToken" not in token:
        return {"ok": False, "error": "invalid expo token"}
    STATE["device_tokens"].add(token)
    return {"ok": True, "registered_tokens": len(STATE["device_tokens"])}

from typing import List, Set, Dict, Any
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

# ── 환경값 ─────────────────────────────────────────────────────────
BEARER = os.environ["X_BEARER_TOKEN"]
QUERY = os.environ.get("QUERY", '(솔음른 배포전 OR 솔음른배포전) -is:retweet lang:ko')
INTERVAL_SEC = int(os.environ.get("INTERVAL_SEC", "1800"))  # 기본 30분
PORT = int(os.environ.get("PORT", "8080"))

# ── 상태 ───────────────────────────────────────────────────────────
STATE: Dict[str, Any] = {"since_id": None, "last_run": None, "device_tokens": set()}  # expo tokens

class RegisterPayload(BaseModel):
    token: str

app = FastAPI()

# ── 유틸 ───────────────────────────────────────────────────────────
def search_once(since_id=None):
    url = "https://api.x.com/2/tweets/search/recent"
    params = {"query": QUERY, "max_results": 10, "tweet.fields": "created_at,lang"}
    if since_id: params["since_id"] = since_id
=======
# ===== 유틸 =====
def search_once(since_id=None):
    url = "https://api.x.com/2/tweets/search/recent"
    params = {"query": QUERY, "max_results": 10, "tweet.fields": "created_at,lang"}
    if since_id:
        params["since_id"] = since_id
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    r = requests.get(url, headers={"Authorization": f"Bearer {BEARER}"}, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def notify_all(title: str, url: str = ""):
<<<<<<< HEAD
    # Expo 푸시: 등록된 모든 토큰으로 발송
    msgs = [{"to": t, "sound": "default", "title": title, "body": url, "data": {"url": url}}
            for t in list(STATE["device_tokens"])]
    if not msgs: return
=======
    if not STATE["device_tokens"]:
        return
    msgs = [{"to": t, "sound": "default", "title": title, "body": url, "data": {"url": url}}
            for t in list(STATE["device_tokens"])]
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    requests.post("https://exp.host/--/api/v2/push/send", json=msgs, timeout=30)

def poll_once():
    try:
        data = search_once(STATE["since_id"])
<<<<<<< HEAD
        meta = data.get("meta", {})
        tweets = data.get("data", [])
        if tweets:
            # 최신 id 업데이트
            latest_id = tweets[0]["id"]
            STATE["since_id"] = latest_id if STATE["since_id"] is None else max(STATE["since_id"], latest_id)
            for tw in reversed(tweets):  # 오래된 것부터
                text = tw.get("text","")
                tid = tw["id"]
                link = f"https://x.com/i/web/status/{tid}"
                notify_all(text, link)
        STATE["last_run"] = int(time.time())
    except requests.HTTPError as e:
        # 429 등은 자연 복구; 로그만
        print("poll error:", e)
=======
        tweets = data.get("data", [])
        if tweets:
            latest_id = tweets[0]["id"]
            STATE["since_id"] = latest_id if STATE["since_id"] is None else max(STATE["since_id"], latest_id)
            for tw in reversed(tweets):  # 오래된 것부터 푸시
                text = tw.get("text", "")
                link = f"https://x.com/i/web/status/{tw['id']}"
                notify_all(text, link)
        STATE["last_run"] = int(time.time())
    except Exception as e:
        print("[poll error]", e)
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)

def loop():
    while True:
        poll_once()
        time.sleep(INTERVAL_SEC)

<<<<<<< HEAD
# ── 라우트 ─────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():  # Render 헬스체크 대응
=======
# ===== 라우트 =====
@app.get("/", include_in_schema=False)
def root():
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    return {"ok": True}

@app.get("/health", include_in_schema=False)
def health():
    return {
<<<<<<< HEAD
        "ok": True,
        "query": QUERY,
        "since_id": STATE["since_id"],
        "last_run": STATE["last_run"],
        "device_tokens": len(STATE["device_tokens"]),
        "interval_sec": INTERVAL_SEC,
=======
        "ok": True, "query": QUERY, "since_id": STATE["since_id"],
        "last_run": STATE["last_run"], "device_tokens": len(STATE["device_tokens"]),
        "interval_sec": INTERVAL_SEC
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    }

@app.head("/", include_in_schema=False)
@app.head("/health", include_in_schema=False)
def head_ok(): return Response(status_code=200)

@app.post("/register")
<<<<<<< HEAD
def register(p: RegisterPayload):
    STATE["device_tokens"].add(p.token)
=======
@app.post("/register-device")
def register_device(p: RegisterPayload = Body(...)):
    token = p.token.strip()
    print("[REGISTER]", token)
    if "ExponentPushToken" not in token:
        return {"ok": False, "error": "invalid expo token"}
    STATE["device_tokens"].add(token)
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
    return {"ok": True, "registered_tokens": len(STATE["device_tokens"])}

@app.post("/test")
def test(req: Request):
    msg = req.query_params.get("msg", "테스트")
    url = req.query_params.get("url", "")
    notify_all(msg, url)
    return {"ok": True}

@app.post("/poll-now")
def poll_now():
    poll_once()
    return {"ok": True, "since_id": STATE["since_id"], "last_run": STATE["last_run"]}

<<<<<<< HEAD
# ── 백그라운드 루프 시작 ──────────────────────────────────────────
=======
# 백그라운드 폴링 시작
>>>>>>> 51efe2b (chore: initial commit with app.py, requirements, Dockerfile)
threading.Thread(target=loop, daemon=True).start()
