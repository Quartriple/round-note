import os
import redis
from rq import Worker, Queue, Connection

# Render에서 주입한 REDIS_URL 환경 변수를 읽습니다.
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Render의 rediss:// (SSL) URL에 맞게 접속 설정을 합니다.
conn = redis.from_url(redis_url, ssl_cert_reqs='required' if redis_url.startswith('rediss://') else None)

if __name__ == '__main__':
    # 'high-priority-queue'라는 이름의 큐를 감시합니다.
    # (FastAPI의 Start Command와 이 큐 이름이 일치해야 합니다.)
    listen = ['high-priority-queue']
    
    print("RQ Worker(일꾼)가 Redis(게시판)를 감시하기 시작합니다...")
    print(f"대상 큐: {listen}")
    
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()