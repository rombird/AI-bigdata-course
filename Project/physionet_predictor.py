"""
PhysioNet 실제 데이터 혈압 예측 머신러닝 모델
AI 프로젝트 수업용 예제 코드

【학습 목표】
1. 실제 PhysioNet 의료 데이터 로드 및 처리
2. 데이터 전처리 및 특성 엔지니어링 기법 이해
3. 여러 모델 비교 및 최적 모델 선택 방법 학습
4. 모델 성능 평가 및 시각화

【사용 기술】
- WFDB: PhysioNet 데이터 읽기
- Scikit-learn: 머신러닝 모델 구현
- Pandas: 데이터 처리
- Matplotlib: 결과 시각화
"""

# ============================================================
# 1. 필요한 라이브러리 임포트
# ============================================================
import pandas as pd
import numpy as np
import platform
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import warnings
import os
import wfdb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeClassifier
from sklearn.metics import mean_absolute_error, r1_score

warnings.fillterwarnings('ignore') # 경고메시지 무시

# ===========================================================
# 2. 메인 클래스
# ===========================================================
class PhysioNetPredictor:
    """
    PhysioNet 실제 데이터를 활용한 혈압 예측 머신러닝 모델 클래스
    
    【주요 기능】
    1. PhysioNet 데이터 로드 (.dat, .hea 파일)
    2. 데이터 전처리 및 특성 엔지니어링
    3. 머신러닝 모델 훈련 및 평가
    4. 새로운 환자 데이터로 혈압 예측
    5. 결과 시각화
    """
    def __init__(self):
        self.models ={}
        self.scaler = StandardScaler
        self.label_encoders ={}
        self.feature_names = []
        self.is_trained = False

    # ============================================================
    # 3. PhysioNet 데이터 로드 메서드
    # ============================================================
    def load_physiconent_data(self, data_dir ="data"):
        """
            PhysioNet 데이터 디렉토리에서 모든 환자 데이터 로드
            
            【매개변수】
            data_dir (str): .dat 및 .hea 파일이 있는 디렉토리 경로
            
            【반환값】
            DataFrame: 로드된 환자 데이터
            
            【데이터 구조】
            - .dat 파일: 실제 생체신호 데이터 (바이너리)
            - .hea 파일: 헤더 정보 (메타데이터)
        """
        print(f'PhysioNet 데이터 로드 중 : {data_dir}')

        # .hea 파일 목록 가져오기
        hea_files = [f for f in os.listdir(data_dir) if f.endswith('.hea')]

        if not hea_files:
            raise FileNotFoundError(f'{data_dir} .hea  파일이 없습니다.')
        
        print(f'발견된 환자 데이터 :  {len(hea_files)}개') # 파일이니까 총 400개 

        all_data = []
        for hea_file in hea_files:
            try:
                # 파일명에서 레코드 이름 추출(ex. 0001.hea -> 0001)
                record_name = hea_file.replace('.hea', '')
                record_path = os.path.join(data_dir, record_name)

                # WFDB를 사용하여 데이터 읽기
                record = wfdb.rdrecord(record_path)

                # 헤더 정보에서 메타 데이터(환자 정보) 추출
                patient_data = self.extract_patient_info(record, record_name)

                if patient_data:
                    all_data.append(patient_data)
            except Exception as e:
                print(f'{hea_file} 로드 실패 : {str(e)}')
                continue
        
        # DataFrame 생성
        df = pd.DataFrame(all_data)

        print(f'{len(df)}개의 환자 데이터 로드 완료!') # 총 몇개의 데이터가 로드됐는지
        print(f'컬럼 : {", ".join(df.columns)}') # 컬럼1, 컬럼2, ... -> 출력형태를 보기 좋게

        return df

    def _extract_patient_info(self, record, record_name):
        """
            WFDB 레코드에서 환자 정보 추출
            
            【매개변수】
            record: WFDB record 객체
            record_name: 레코드 이름
            
            【반환값】
            dict: 환자 정보 딕셔너리
        """
        try:
            # 기본정보
            patient_data = {
                'patient_id' : record_name,
                'sampling_rate' : record.fs,
                'signal_length' : record.sig_len,
            }
            # 신호 데이터에서 통계 추출
            if record.p_signal is not None and len(record.p_signal) > 0:
                # 각 신호 채널별 평균, 표준편차, 최대값, 최소값 계산
                for i, sig_name in enumerate(record.sig_name):
                    signal_data = record.p_signal[:, i] 
                    patient_data[f'{sig_name}_mean'] = np.mean(signal_data)
                    patient_data[f'{sig_name}_std'] = np.std(signal_data)
                    patient_data[f'{sig_name}_max'] = np.max(signal_data)
                    patient_data[f'{sig_name}_min'] = np.min(signal_data)
            
            # 주석(comments)에서 추가 정보 추출
            if hasattr(record, 'comments') and record.comments:
                for comment in record.comments:
                    if ':' in comment: # 만약 : 이 있다면(key와 value가 있다면) -> :를 기준으로 value만 추출
                        # ex) '질병' : '당뇨' = key : value
                        key, value = comment.split(':', 1) # 여러 항목이 있을 수도 있으니까 :를 기준으로 첫번째꺼만
                        patient_data[key.strip()] = value.strip() # key 주변에 공백을 사전 제거해서 -> 이런 형태로 patient_data['질병'] = '당뇨'
            return patient_data
        except Exception as e:
            print(f'환자 정보 추출 실패 ({record_name}) : {str(e)}')
            return None
        
    # ============================================================
    # 4. 데이터 전처리 메서드
    # ============================================================
    def preprocess_data(self, df):
        """
        데이터 전처리 및 이상치 처리
        
        【주요 작업】
        1. 결측값 처리
        2. 무한대 값 제거
        3. IQR 방법으로 극단적 이상치 제거
        4. 범주형 변수 인코딩
        5. 특성 엔지니어링
        """
        print("🔄 데이터 전처리 중...")

        # 1. 결측값 처리
        if df.isnull().sum().sum() > 0: # 결측값의 총 합이 0보다 크면 결측값이 있다는 의미
            print('결측값 발견, 처리중 ...')
            # 숫자형 : 중앙값으로 채움
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

            # 범주형 : 최빈값으로 채움(제일 자주 등장)
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown') # 최빈값이 비지 않았다면 mode()[0]를 사용하고 비었다면 Unknown으로 출력해라