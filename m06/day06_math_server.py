# 로깅 기능을 위한 모듈 가져오기
import logging

# FastMCP 서버를 사용하기 위한 클래스 가져오기
from mcp.server.fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(level=logging.INFO) 

# MCP 서버 인스턴스 생성('Math'는 이 MCP 서버 이름)
mcp = FastMCP('Math')

# 도구 1 : 더하기 함수
@mcp.tool()
def add(a: int, b:int) -> int:
    """더하기 툴"""
    try:
        a = int(a) # 입력값을 정수로 변환
        b = int(b)
        logging.info(f'Adding {a} and {b}') # 로그 출력
        return a+b # 더한 결과 반환
    except Exception as e:
        # 예외 발생 시 에러 로그 출력 후 다시 예외 발생 시킴
        logging.error(f'Error in add:{e}')
        raise

# 도구 2 : 빼기 함수
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """빼기 툴"""
    try:
        a = int(a)
        b = int(b)
        logging.info(f'Subtarcting {a} from {b}') # 로그 출력
        return a - b
    except Exception as e:
        logging.error(f'Error in subtarct : {e}')
        raise

# 메인 실행 구문 : MCP 서버를 studio 방식으로 실행
if __name__ =='__main__':
    map.run(transport='stdio')
    