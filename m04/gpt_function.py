# 도시별 시간 알려주기 - 문자열 형식으로 받은 타임존을 시각으로 구하기
# ex) 서울 -> 오후 8시 20분

from datetime import datetime
import pytz

# timezone이라는 매개변수에 대한 힌트 : str이라고 명시 
def get_current_time(timezone: str='Asia/Seoul'):
    """GPT가 현재 시간을 파악할 수 있게 해주는 함수 - 현재 시간 출력(반환)"""
    tz = pytz.timezone(timezone) # 타임존 설정
    # 타임존에 맞는 현재시간 -> 형식에 맞춘다 -> now변수에 담는다
    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S') # 포맷에 맞춰 출력
    now_timezone = f'{now} {timezone}'
    print(now_timezone)
    return now_timezone

tools = [
    {
        'type':'function',
        'function':{
            'name':'get_current_time',
            'description':'해당 타임존의 날짜와 시간을 반환합니다.',
            'parameters':{
                'type':'object',
                'properties':{
                    'timezone':{
                        'type':'string',
                        'description':'현재날짜와 시간을 반환할 타임존을 입력하세요.(예:Asia/Seoul)'
                    },
                },
                'required':['timezone'],
            },
        },
    }
]

# __name__ : 메인함수 개념
# 파이썬 파일을 모듈로서 사용(다른 파일에서 불러와 사용하는 경우 __name__에 모듈 이름이 설정)
# 다른파일에서 get_current_time('America/New_York') 호출되지 않도록 이 파일안에서만 호출되도록 하겠다는 의미
if __name__ == '__main__':
    get_current_time('America/New_York') 

print(__name__) # 결과 : __main__ 