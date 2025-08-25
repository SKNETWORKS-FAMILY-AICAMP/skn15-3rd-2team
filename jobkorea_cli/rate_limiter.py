# rate_limiter.py
import time, asyncio, random

class TokenBucket:
    """
    토큰 버킷 기반 Rate Limiter
    - rate_per_sec: 초당 허용 요청 수
    - burst: 순간적으로 허용할 최대 요청 수
    """
    def __init__(self, rate_per_sec=1.0, burst=2):
        self.rate = rate_per_sec
        self.capacity = burst
        self.tokens = burst
        self.ts = time.monotonic()
        self.lock = asyncio.Lock()

    async def take(self):
        """
        요청 전 호출해서 속도 제어.
        토큰이 없으면 기다렸다가 다시 시도.
        """
        async with self.lock:
            now = time.monotonic()
            delta = now - self.ts
            self.ts = now
            # 시간이 흐른만큼 토큰 채우기
            self.tokens = min(self.capacity, self.tokens + delta * self.rate)

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

async def polite_sleep(ms_base=600, jitter=0.4):
    """
    크롤링 예의 지연.
    ms_base ± jitter 비율의 랜덤 sleep.
    예: polite_sleep(1200, 0.5) → 600~1800ms 사이 랜덤 대기
    """
    ms = ms_base * (1 + (random.random()*2 - 1)*jitter)
    await asyncio.sleep(ms/1000)
