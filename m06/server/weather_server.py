from fastmcp import FastMCP
import httpx, os
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# 기본 env를 덮어쓰기 - 중간에 key 생성시마다 업데이트
PROJECT_ROOT = Path(__file__).resolve().parents[1] # 파일경로 MCP_ENV 
ENV_PATH = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=ENV_PATH, override=True) # 덮어쓰기 true

mcp = FastMCP('Weather')

# 환경변수가 설정되어있지 않을때 예외처리
# 함수명에서 _ : private 한 함수라는 의미
def _require_key() -> str: # return시 자료형 str
    """환경변수에서 OpenWeather API 키를 가져옴"""
    key = os.getenv('OPENWEATHER_API_KEY')
    if not key:
        raise RuntimeError("OPENWEATHER_API_KEY 환경변수가 설정되지 않았습니다") # RuntimeError : 실제 실행 에러
    return key # 키가 제대로 있으면 key(문자열) 반환

# 비동기함수 정의
async def _get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """비동기 HTTP GET 요청을 보내고 JSON 응답을 반환"""
    timeout = httpx.Timeout(10.0) # 10초 타임아웃 설정
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params) # 비동기함수를 먼저 만들어놓고 내가 실행하고 싶을 때 요청
        r.raise_for_status() # HTTP 오류 발생시 예외 발생
        return r.json() # json응답을 리턴

def _iso_from_unix_with_offset(unix_ts: int, offset_seconds: int) -> str: # 시간대를 표준으로 가져오겠다
    """유닉스 타임스탬프와 오프셋을 사용하여 ISO 8601 형식의 날짜 문자열 생성"""
    tz = timezone(timedelta(seconds=offset_seconds)) 
    return datetime.fromtimestamp(unix_ts, tz).isoformat() # 표준화 형식

# 현재 날씨 조회 - 비동기함수로
@mcp.tool
async def current(
    city: str,
    country: Optional[str] = None, # country는 있어도 되고 없어도 됨
    units: str = 'metric', # metric(℃, m/s) | imperial(℉, mph)
    lang: str = 'kr'
) -> Dict[str, Any]:
    """현재 날씨 정보를 반환"""
    key = _require_key()
    q = f'{city}, {country}' if country else city # country가 true(country 값이 있으면) -> f'' 출력, 아니면 city만 q에 담기
    params = {'q':q, 'appid':key, 'units':units, 'lang':lang} # site API 문서 형태 따름
    url = 'https://api.openweathermap.org/data/2.5/weather'

    try:
        data = await _get_json(url, params)
    except httpx.HTTPError as e:
        return {'error' : f'HTTP {e.response.status_code} : {e.response.text}'}
    except Exception as e:
        return {'error' : str(e)}
    
    weather = (data.get('weather') or [{}])[0]
    main = data.get('main', {})
    wind = data.get('wind', {})
    sys = data.get('sys', {})
    coord = data.get('coord', {})
    tz_offset = data.get('timezone', 0)
    dt_unix = data.get('dt')
    iso_time = _iso_from_unix_with_offset(dt_unix, tz_offset) if dt_unix else None

    result = {
        "city": data.get("name"),
        "country": sys.get("country"),
        "coord": {"lat": coord.get("lat"), "lon": coord.get("lon")},
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),   # metric: m/s, imperial: mph
        "wind_deg": wind.get("deg"),
        "weather": weather.get("description"),
        "icon": weather.get("icon"),
        "time_local": iso_time,
        "units": units,
        "source": "openweathermap",
    }

@mcp.tool
async def forecast(
    city: str,
    country: Optional[str] = None,
    days: int = 3,
    units: str = 'metric', # metric(℃, m/s), imperial(℉, mph), standard(K)
    lang: str = 'kr'
) -> Dict[str, Any]:
    """날씨 예보 정보를 반환"""
    key = _require_key()
    days = 1 if days < 1 else 5 if days > 5 else days # 1 ~ 5일 사이로 제한
    q = f'{city}, {country}' if country else city
    params = {'q': q, 'appid' : key, 'units': units, 'lang' : lang}
    url= 'https://api.openweathermap.org/data/2.5/forecast'

    try:
        data = await _get_json(url, params)
    except httpx.HTTPError as e:
        return {"error" : f'HTTP {e.response.status_code} : {e.response.text}'}
    except Exception as e:
        return {'error' : str(e)}
    list: List[Dict[str, Any]] = data.get('list', [])
    city_info = data.get('city', {})
    tz_offset = city_info.get('timezone', 0)
    name = city_info.get('name') or city
    country = city_info.get('country')
    coord = city_info.get('coord', {})

    # 로컬 날짜 기준으로 그룹핑
    by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in list:
        dt_unix = item.get("dt")
        if dt_unix is None:
            continue
        iso = _iso_from_unix_with_offset(dt_unix, tz_offset)
        local_date = iso[:10]  # YYYY-MM-DD
        by_date[local_date].append(item)

    summaries = []
    for d in sorted(by_date.keys())[:days]:
        items = by_date[d]
        temps = [it.get("main", {}).get("temp") for it in items if it.get("main")]
        temp_min = min([it.get("main", {}).get("temp_min") for it in items if it.get("main")], default=None)
        temp_max = max([it.get("main", {}).get("temp_max") for it in items if it.get("main")], default=None)
        descs = [ (it.get("weather") or [{}])[0].get("description") for it in items ]
        cnt = Counter([x for x in descs if x])
        desc = cnt.most_common(1)[0][0] if cnt else None

        summaries.append({
            "date": d,
            "temp_avg": (sum(t for t in temps if t is not None) / len(temps)) if temps else None,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "weather": desc,
        })

    return {
        "city": name,
        "country": country,
        "coord": {"lat": coord.get("lat"), "lon": coord.get("lon")},
        "units": units,
        "days": summaries,
        "source": "openweathermap",
    }

if __name__ == '__main__':
    mcp.run(transport='stdio') # 로컬에서 돌린다는 의미