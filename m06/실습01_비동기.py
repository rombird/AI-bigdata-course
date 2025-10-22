# 동기 함수 : 호출하면 바로 실행 (일반적인 함수)
# 비동기 함수 : 호출하면 바로 실행 X, 나중에 실행(예약)

import asyncio

# async 예약어 사용시 -> 이 함수는 비동기 함수로 처리
async def hello():
    return "안녕하세요!"

print(asyncio.run(hello())) # hello() 예약 -> hello() 실행 -> return 값 반환
