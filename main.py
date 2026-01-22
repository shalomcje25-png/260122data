import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="서울 기온 비교 분석기", layout="wide")

# 데이터 로딩 및 전처리 함수
def load_and_preprocess(main_file, uploaded_file=None):
    # 기본 데이터 로드 (기존 7줄 건너뛰기 유지)
    df_main = pd.read_csv(main_file, skiprows=7)
    
    if uploaded_file:
        df_new = pd.read_csv(uploaded_file, skiprows=7)
        df = pd.concat([df_main, df_new], ignore_index=True)
    else:
        df = df_main
    
    # 전처리: 날짜 정리 및 타입 변환
    df['날짜'] = df['날짜'].astype(str).str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    df = df.dropna(subset=['평균기온(℃)']) # 결측치 제거
    
    # 월/일 정보 추출
    df['month_day'] = df['날짜'].dt.strftime('%m-%d')
    return df.sort_values('날짜')

# 사이드바: 파일 업로드
st.sidebar.header("데이터 설정")
uploaded_file = st.sidebar.file_uploader("추가 기온 데이터 업로드 (CSV)", type="csv")

try:
    df = load_and_preprocess('20260122.csv', uploaded_file)
    
    st.title("🌡️ 과거 동일 날짜 대비 기온 분석")
    st.info("선택한 날짜의 기온이 역대 같은 날짜들의 평균에 비해 어떠했는지 분석합니다.")

    # 날짜 선택 (기본값: 가장 최근 날짜)
    max_date = df['날짜'].max()
    target_date = st.date_input("비교할 날짜를 선택하세요", value=max_date, 
                               min_value=df['날짜'].min(), max_value=max_date)
    
    # 데이터 필터링
    target_md = target_date.strftime('%m-%d')
    same_day_history = df[df['month_day'] == target_md]
    
    # 선택한 날 데이터와 역대 평균 데이터
    target_row = same_day_history[same_day_history['날짜'] == pd.to_datetime(target_date)]
    
    if not target_row.empty:
        target_temp = target_row['평균기온(℃)'].values[0]
        avg_temp = same_day_history['평균기온(℃)'].mean()
        diff = target_temp - avg_temp
        
        # 1. 지표 출력
        col1, col2, col3 = st.columns(3)
        col1.metric("선택 날짜 기온", f"{target_temp}℃")
        col2.metric("역대 동일 날짜 평균", f"{avg_temp:.2f}℃")
        col3.metric("차이", f"{diff:.2f}℃", delta=f"{diff:.2f}℃", delta_color="normal")
        
        st.write(f"### 📊 역대 {target_md}의 기온 변화 추이")
        
        # 2. Plotly 그래프 생성
        fig = go.Figure()
        
        # 역대 기온 선 그래프
        fig.add_trace(go.Scatter(
            x=same_day_history['날짜'], 
            y=same_day_history['평균기온(℃)'],
            mode='lines+markers',
            name='평균기온',
            line=dict(color='#1f77b4'),
            hovertemplate='%{x|%Y년}<br>기온: %{y}℃'
        ))
        
        # 선택한 날짜 강조점
        fig.add_trace(go.Scatter(
            x=[pd.to_datetime(target_date)],
            y=[target_temp],
            mode='markers',
            name='선택한 날짜',
            marker=dict(color='red', size=12, symbol='star'),
            hovertemplate='선택한 날: %{y}℃'
        ))
        
        # 평균선 추가
        fig.add_hline(y=avg_temp, line_dash="dash", line_color="green", 
                     annotation_text=f"역대 평균: {avg_temp:.2f}℃")

        fig.update_layout(
            xaxis_title="연도",
            yaxis_title="기온 (℃)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("선택한 날짜의 데이터가 존재하지 않습니다.")

except FileNotFoundError:
    st.error("기본 데이터 파일(`20260122.csv`)을 찾을 수 없습니다. 경로를 확인해주세요.")
