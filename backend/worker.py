import os
import redis
from rq import Worker, Queue

print("RQ Worker(일꾼) 프로세스가 시작됩니다...")

# Render에서 주입한 REDIS_URL 환경 변수를 읽습니다.
redis_url = os.getenv('REDIS_URL')

if not redis_url:
    print("에러: REDIS_URL 환경 변수가 설정되지 않았습니다.")
    exit(1)

# Render의 rediss:// (SSL) URL에 맞게 접속 설정을 합니다.
conn = None
try:
    if redis_url.startswith("rediss://"):
        conn = redis.from_url(redis_url, ssl_cert_reqs='required')
    else:
        conn = redis.from_url(redis_url)
    
    conn.ping()
    print("Redis에 성공적으로 연결되었습니다.")
except Exception as e:
    print(f"Redis 연결 실패: {e}")
    exit(1)

# --- [수정] 작업(Task)을 worker.py에 정의합니다. ---
def example_task(message):
    """
    FastAPI가 요청한 실제 작업.
    이 로그가 찍히면 Sprint 0 성공입니다!
    """
    print("--- [작업 수신 성공] ---")
    print(f"RQ Worker received message: {message}")
    print("--- [작업 완료] ---")
    return f"Message processed: {message}"

if __name__ == '__main__':
    # 'high-priority-queue'라는 이름의 큐를 감시합니다.
    listen = ['high-priority-queue']
    
    print(f"'{listen}' 큐를 감시합니다. 새 작업을 기다립니다...")
    
    # 1. 큐 객체들을 생성합니다.
    queues = [Queue(name, connection=conn) for name in listen]
    
    # 2. 워커를 생성하고 큐와 연결 객체를 전달합니다.
    worker = Worker(queues, connection=conn)
    
    # 3. work()는 무한 루프입니다.
    worker.work()