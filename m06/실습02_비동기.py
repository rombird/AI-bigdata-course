# asyncio 함수 안에서는 await를 써야 실제 신행이 진행된다.
# await는 '여기서 잠깐 멈췄다가 결과가 준비되면 이어서 진행해줘'라는 의미

import asyncio

async def hello():
    await asyncio.sleep(1) # 1초 기다림
    return '안녕하세요!'

async def main():
    msg = await hello() # 실제 실행
    print(msg)

asyncio.run(main()) 