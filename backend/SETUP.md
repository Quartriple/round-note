# Backend 환경 설정 가이드

## Docker 환경 설정

Docker Compose를 사용하여 백엔드를 실행하기 전에 환경 변수를 설정해야 합니다.

### 1. .env.docker 파일 생성

```bash
# backend 디렉토리에서
cp .env.docker.example .env.docker
```

### 2. .env.docker 파일에 실제 API 키 입력

`.env.docker` 파일을 열고 다음 항목들을 실제 값으로 교체하세요:

#### 필수 API 키
- `DEEPGRAM_API_KEY`: Deepgram 음성 인식 API 키
- `ELEVENLABS_API_KEY`: ElevenLabs TTS API 키
- `OPENAI_API_KEY`: OpenAI API 키

#### NCP Object Storage
- `NCP_ENDPOINT_URL`: NCP Object Storage 엔드포인트
- `NCP_BUCKET_NAME`: 버킷 이름
- `NCP_ACCESS_KEY`: NCP Access Key
- `NCP_SECRET_KEY`: NCP Secret Key

#### Google OAuth
- `GOOGLE_CLIENT_ID`: Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth Client Secret

#### 보안 키 (반드시 변경)
- `SECRET_KEY`: JWT 토큰 서명용 비밀 키
- `ENCRYPTION_KEY`: 데이터 암호화 키
  - 생성 방법: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### 3. Docker Compose 실행

```bash
docker-compose up -d
```

## 보안 주의사항

- `.env.docker` 파일은 절대 Git에 커밋하지 마세요 (이미 .gitignore에 추가됨)
- 실제 API 키와 비밀 값은 안전하게 보관하세요
- 프로덕션 환경에서는 환경 변수를 안전한 방법으로 주입하세요 (AWS Secrets Manager, Azure Key Vault 등)
