# 간단한 수학 계산기 MCP 서버를 구현 - 입력으로 받은 수식을 파싱하고 안전하게 평가한 뒤 결과 반환

# conda install langgraph langchain-openai langchain-mcp-adapters fastmcp python-dotenv httpx
# .env 파일에 CONTEXT7_API_KEY, OPENAI_API_KEY 설정 필요
from fastmcp import FastMCP
import ast, opeartor as op
from pathlib import Path # 경로설정
from dotenv import load_dotenv

# .env 파일에 계속해서 key를 추가할 경우 계속해서 업데이트 처리해주겠다
# (코드 중간에 .env에 새로운 key를 추가할 경우 새로운 key를 못읽기 때문에)
PROJECT_ROOT=Path(__file__).resolve().parent[1]
ENV_PATH = PROJECT_ROOT/'.env'
load_dotenv(dotenv_path=ENV_PATH, override=True) # override (무조건 덮어쓰겠다) -> 코드 어디에서든 접근 가능하도록

mcp = FastMCP('math') # 우리가 만드는 서버이름 math (MCP 서버 인스턴스 생성)
OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow,
    ast.USub: op.neg, ast.UAdd: op.pos, ast.BitXor: op.xor 
}

def _eval_ast(node):
    """예외처리를 위한 구문 -> AST 노드 평가"""
    if isinstance(node, ast.Num):  # py<=3.7
        return node.n
    if isinstance(node, ast.Constant):  # py>=3.8
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("숫자만 허용됩니다.")
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        fn = OPS.get(type(node.op))
        if not fn:
            raise ValueError(f"허용되지 않은 연산자: {type(node.op).__name__}")
        return fn(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand)
        fn = OPS.get(type(node.op))
        if not fn:
            raise ValueError(f"허용되지 않은 단항 연산자: {type(node.op).__name__}")
        return fn(operand)
    raise ValueError(f"허용되지 않은 표현식: {type(node).__name__}")

# mcp.tool 데코레이터 : FastMCP 라이브러리의 기능으로 아래 정의된 함수를 MCP 프로토콜로 외부에 노출하는 역할
@mcp.tool
def eval(expression: str) -> dict:
    """
    안전한 수식평가(사칙연산/거듭제곱/나머지/정수나눗셈)
    예) "3*(5+2) - 10/2"
    """
    try:
        tree = ast.parse(expression, mode='eval') # 파이썬에서 eval 함수 이미 존재
        value = _eval_ast(tree.body)
        return {"value":value} # 계산이 성공하면 딕셔너리 반환
    except Exception as e:
        return {'error':str(e)} # error 메시지는 문자형으로 형변환해서 값으로 나오도록

# __name__ : 현재위치를 알려줌 
if __name__ == "__main__": # 현재위치는 main임을 알려줌
    mcp.run()