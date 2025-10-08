markdown
# x-monitor (솔음른 배포전 / 솔음른배포전 알림)

X(트위터) 검색 `recent` API로 아래 키워드의 **새 게시물만** 감지해 푸시/웹훅으로 알림합니다.

- `솔음른 배포전`
- `솔음른배포전`
- 기본 쿼리: `(솔음른 배포전 OR 솔음른배포전) -is:retweet lang:ko`

## 기능
- `since_id`를 파일로 저장 → **재시작 후에도 이어서** 새 글만 알림
- **콜드 스타트 시 알림 차단**: 최초 기동 때 과거 글 대량 알림 방지
- Expo 푸시(기본) / Discord 웹훅 선택 (`NOTIFY_MODE`)
- `/health`, `/poll-now`, `/register`, `/test` 엔드포인트

## 환경변수
- `X_BEARER_TOKEN` (필수): X API v2 Bearer Token
- `QUERY` (옵션): 기본값은 위 쿼리
- `INTERVAL_SEC` (옵션, 기본 60초)
- `MAX_RESULTS` (옵션, 기본 50)
- `SINCE_FILE` (옵션, 기본 `since_id.txt`)
- `NOTIFY_MODE` (옵션, `expo` | `discord`, 기본 `expo`)
- `DISCORD_WEBHOOK_URL` (옵션, `NOTIFY_MODE=discord`일 때 필수)

## 로컬 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export X_BEARER_TOKEN="YOUR_TOKEN"
uvicorn app:app --reload
```

### 테스트
- 헬스: `GET http://localhost:8000/health`
- 수동 폴링: `POST http://localhost:8000/poll-now`
- 푸시 테스트: `POST http://localhost:8000/test?msg=hello&url=https://x.com`

## Render 배포
- Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- 환경변수에 `X_BEARER_TOKEN` 추가
- 무료 플랜은 15분 무트래픽시 sleep → UptimeRobot 등으로 `/health` 12분 주기 ping 권장

## Expo 푸시 등록
클라이언트에서 받은 `ExponentPushToken[...]`을 아래로 POST:
```bash
curl -X POST https://<YOUR-RENDER-URL>/register \
  -H "Content-Type: application/json" \
  -d '{"token":"ExponentPushToken[xxxxxxxxxxxxxx]"}'
```

## Discord 웹훅 사용
환경변수:
```
NOTIFY_MODE=discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/.../...
```
