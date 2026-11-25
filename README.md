# hannun-status

한눈 앱이 켜질 때 읽는 **버전 상태 파일**이에요. 이 저장소에는 서명된 `status.json`만 올라가고, 개인정보나 비밀 키는 없어요.

앱은 `https://raw.githubusercontent.com/junha8070/hannun-status/main/status.json` 한 곳에서 GET으로만 읽어요. 아무 정보도 보내지 않아요.

## 보안 원칙
- `status.json`은 개발자 컴퓨터에만 있는 비밀 키(ECDSA P-256)로 서명돼요. 앱은 서명이 맞을 때만 믿어요.
  깃허브 계정이 털려 누가 파일을 바꿔도, 서명이 틀리면 앱은 무시해요.
- 예전 파일을 다시 올려도(되돌리기) 앱이 거부해요. `issuedAt`은 항상 지난번보다 커야 해요(스크립트가 알아서 맞춰요).
- '새 버전 받기' 주소는 `https://play.google.com`, `https://github.com`만 허용돼요.
- **비밀 키(`status_private.pem`)는 이 저장소에 절대 넣지 마세요.** `.gitignore`가 `*.pem`을 막고, 스크립트도 키가 저장소 안에 있으면 멈춰요.
- 비밀 키는 USB나 비밀번호 관리자에 따로 백업해 두세요. 잃어버리면 앱 업데이트로 새 공개 키를 넣기 전까지 상태를 바꿀 수 없어요.
- 깃허브 계정은 2단계 인증을 켜 두세요.

## 사용법
1. `policy.json`을 고쳐요.
2. `python3 sign_status.py`를 실행하면 서명된 `status.json`이 생겨요.
3. `status.json`(과 바꾼 `policy.json`)을 main 브랜치에 커밋·푸시해요. 앱에는 보통 몇 분 안에 반영돼요(앱은 켤 때, 그리고 6시간마다 확인해요).

### 특정 버전 막기 (예: 안드로이드 1.0.1에 문제)
```json
"android": { "blocked": ["1.0.1"], "latest": "1.0.2", "url": "https://play.google.com/store/apps/details?id=com.xlntsmmr.invest" },
"title": "이 버전은 지금 쓸 수 없어요",
"message": "1.0.1에서 잔고가 잘못 보이는 문제가 있어 멈췄어요. 1.0.2로 업데이트해 주세요."
```

### 이 버전보다 낮으면 모두 막기
```json
"android": { "minVersion": "1.1.0" }
```

### 전부 멈추기 (예: 한국투자 정책 문제로 급히 멈춰야 할 때)
```json
"blockAll": true
```

### 새 버전 안내만 하기 (막지 않음)
```json
"desktop": { "latest": "1.1.0", "url": "https://github.com/junha8070/hannun-status/releases" }
```

### 다시 풀기
`blocked`에서 지우거나 `blockAll`을 `false`로 바꾸고 다시 서명·푸시하면 돼요.

## 막혔을 때 앱에서 일어나는 일
- 다른 화면 대신 안내 화면만 보이고, 한국투자 접속(위젯·백그라운드 알림 포함)도 멈춰요.
- 기기에 저장된 키·관심종목은 그대로 있어요. 새 버전을 깔면 그대로 이어서 써요.
- 오프라인이어도 마지막으로 받은 상태를 기억해서 계속 적용돼요.
- 안드로이드(플레이 설치본)는 플레이의 '즉시 업데이트' 화면도 함께 떠요.
  플레이 콘솔에서 출시할 때 업데이트 우선순위를 4 이상으로 주면, 상태 파일 없이도 즉시 업데이트를 띄워요.
