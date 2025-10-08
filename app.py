
import os
import time
import threading
import requests
from typing import Dict, Any, Optional, Set

from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from urllib.parse import unquote

QUERY = os.environ.get("QUERY")
if os.environ.get("QUERY_B64"):
    try:
        QUERY = base64.b64decode(os.environ["QUERY_B64"]).decode("utf-8")
    except Exception as e:
        print("Base64 decode error:", e)

if os.environ.get("QUERY_URLENC"):
    try:
        QUERY = urllib.parse.unquote(os.environ["QUERY_URLENC"])
    except Exception as e:
        print("URL decode error:", e)


if QUERY and "�" in QUERY:
    try:
        QUERY = QUERY.encode("latin1").decode("utf-8")
    except Exception as e:
        print("latin1→utf8 재복원 실패:", e)

print("✅ Loaded QUERY:", QUERY)
# (선택) URL 인코딩 대체키도 지원하려면:
if os.environ.get("QUERY_URLENC"):
    QUERY = unquote(os.environ["QUERY_URLENC"])


# =====================
# Config (ENV)
# =====================
BEARER = os.environ["X_BEARER_TOKEN"]  # required
QUERY = os.environ.get("QUERY", "(솔음른 배포전 OR 솔음른배포전) -is:retweet lang:ko")
INTERVAL_SEC = int(os.environ.get("INTERVAL_SEC", "60"))
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "50"))
SINCE_FILE = os.environ.get("SINCE_FILE", "since_id.txt")

# notification: expo (default) or discord
NOTIFY_MODE = os.environ.get("NOTIFY_MODE", "expo").lower()
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# =====================
# App & CORS
# =====================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterPayload(BaseModel):
    token: str  # Expo push token (ExponentPushToken[...])

STATE: Dict[str, Any] = {
    "since_id": None,
    "last_run": None,
    "cold_start": True,
    "device_tokens": set(),   # Set[str]
    "backoff_until": 0,
}

# =====================
# Persistence
# =====================
def load_since_id() -> Optional[str]:
    if os.path.exists(SINCE_FILE):
        try:
            with open(SINCE_FILE, "r") as f:
                sid = f.read().strip()
                if sid:
                    return sid
        except Exception as e:
            print("[load_since_id error]", e)
    return None

def save_since_id(sid: str) -> None:
    try:
        with open(SINCE_FILE, "w") as f:
            f.write(str(sid))
    except Exception as e:
        print("[save_since_id error]", e)

persisted = load_since_id()
if persisted:
    STATE["since_id"] = persisted
    STATE["cold_start"] = False

# =====================
# X (Twitter) search v2
# =====================
def search_recent(since_id: Optional[str]) -> Dict[str, Any]:
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": QUERY,
        "max_results": MAX_RESULTS,
        "tweet.fields": "created_at,lang,author_id",
    }
    if since_id:
        params["since_id"] = since_id  # newer than since_id
    r = requests.get(url, headers={"Authorization": f"Bearer {BEARER}"}, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# =====================
# Notifiers
# =====================
def notify_expo(title: str, url: str = "") -> None:
    tokens: Set[str] = STATE["device_tokens"]
    if not tokens:
        return
    msgs = [{"to": t, "sound": "default", "title": title, "body": url, "data": {"url": url}} for t in list(tokens)]
    try:
        requests.post("https://exp.host/--/api/v2/push/send", json=msgs, timeout=30)
    except Exception as e:
        print("[expo notify error]", e)

def notify_discord(title: str, url: str = "") -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {"content": f"{title}\n{url}".strip()}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)
    except Exception as e:
        print("[discord notify error]", e)

def notify_all(title: str, url: str = "") -> None:
    if NOTIFY_MODE == "discord":
        notify_discord(title, url)
    else:
        notify_expo(title, url)

# =====================
# Poller
# =====================
def poll_once() -> None:
    now = int(time.time())
    if STATE["backoff_until"] and now < STATE["backoff_until"]:
        return
    try:
        data = search_recent(STATE["since_id"])
        tweets = data.get("data", []) or []
        if tweets:
            newest_id = max(t["id"] for t in tweets)
            if STATE["cold_start"] and STATE["since_id"] is None:
                save_since_id(newest_id)
                STATE["since_id"] = newest_id
                STATE["cold_start"] = False
            else:
                for tw in reversed(tweets):  # oldest -> newest
                    tid = tw["id"]
                    text = tw.get("text", "")
                    link = f"https://x.com/i/web/status/{tid}"
                    notify_all(text, link)
                save_since_id(newest_id)
                STATE["since_id"] = newest_id
        STATE["last_run"] = int(time.time())
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        print("[poll http error]", status, e)
        if status == 429:
            STATE["backoff_until"] = int(time.time()) + 120
    except Exception as e:
        print("[poll error]", e)

def loop() -> None:
    while True:
        poll_once()
        time.sleep(INTERVAL_SEC)

# =====================
# Routes
# =====================
@app.get("/", include_in_schema=False)
def root():
    return {"ok": True}

@app.get("/health", include_in_schema=False)
def health():
    return {
        "ok": True,
        "query": QUERY,
        "since_id": STATE["since_id"],
        "last_run": STATE["last_run"],
        "interval_sec": INTERVAL_SEC,
        "cold_start": STATE["cold_start"],
        "notify_mode": NOTIFY_MODE,
        "registered_tokens": len(STATE["device_tokens"]),
        "backoff_until": STATE["backoff_until"],
    }

@app.head("/", include_in_schema=False)
@app.head("/health", include_in_schema=False)
def head_ok():
    return Response(status_code=200)

@app.post("/register")
@app.post("/register-device")
def register_device(p: RegisterPayload = Body(...)):
    token = p.token.strip()
    if not token:
        return {"ok": False, "error": "empty token"}
    STATE["device_tokens"].add(token)
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

# background thread
threading.Thread(target=loop, daemon=True).start()
