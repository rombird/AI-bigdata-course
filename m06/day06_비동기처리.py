import asyncio, time

# # 동기
# def sync_work():
#     time.sleep(1)
#     return '동기 끝!'

# # 비동기
# async def async_work():
#     await asyncio.sleep(1)
#     return '비동기 끝!'

# async def main():
#     print('동기 실행!')
#     print(sync_work())
#     print('비동기 실행!')
#     tasks = [async_work(), async_work(), async_work()]
#     result = await asyncio.gather(*tasks)
#     print(result)

# asyncio.run(main())

# --------------------------------------------------
# 두 도시(서울, 부산)의 날씨를 동시에 가져오기
import asyncio
import random

# 날씨를 가져오는 비동기 함수(API 대신 sleep으로 시뮬레이션)
async def get_weather(city):
    print(f'{city}의 날씨를 가져오는 중...')
    await asyncio.sleep(random.uniform(1, 3)) # 1 ~ 3초 랜덤 대기(지연)
    temp = random.randint(-5, 35) # 임의의 온도
    return f'{city}의 현재 온도는 {temp}ºC 입니다.'

async def main():
    # 동시에 실행할 작업 목록
    tasks = [
        get_weather('서울'),
        get_weather('부산')
    ]

    # 동시에 실행하고 결과 모으기
    results = await asyncio.gather(*tasks)
    print('=====결과=====')
    for r in results:
        print(r)

asyncio.run(main())