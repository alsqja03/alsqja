import streamlit as st
import pandas as pd
from datetime import time, timedelta

# --- 1. 기본 설정 및 데이터 구조 생성 ---

st.set_page_config(layout="wide") # 넓은 화면 레이아웃 사용
st.title("🧑‍💻 수강신청 시간표 도우미")

# session_state 초기화: 사용자가 추가한 과목 목록을 저장
if 'courses' not in st.session_state:
    st.session_state.courses = []

# --- 여기부터 수정된 부분 ---

# 시간표의 시간 인덱스 생성 (08:00 ~ 19:30, 30분 간격)
time_index = []
current_time = time(8, 0)
end_time = time(19, 30)

while current_time <= end_time:
    time_str = current_time.strftime('%H:%M')
    
    # 시간 레이블 생성 로직 수정 (더 간결하고 정확하게)
    if current_time.minute == 0:
      # 교시 번호 (0, 1, 2, ...)를 시간에서 직접 계산
      class_period = current_time.hour - 8
      label = f"{class_period} ({time_str})"
    else:
      label = f".5 ({time_str})"

    time_index.append(label)
    
    # 30분 증가
    current_time = (pd.to_datetime(f'2024-01-01 {current_time}') + timedelta(minutes=30)).time()

# --- 여기까지 수정된 부분 ---

# 시간표의 요일 컬럼
days = ['월', '화', '수', '목', '금', '토', '일']

# 빈 시간표 DataFrame 생성
schedule_df = pd.DataFrame('', index=time_index, columns=days)

# --- 2. 사용자 입력 (사이드바) ---

st.sidebar.header("과목 추가하기")
course_name = st.sidebar.text_input("과목명", placeholder="예: 파이썬 기초")
selected_day = st.sidebar.selectbox("요일", days)
start_time_str = st.sidebar.selectbox("시작 시간", time_index)
end_time_str = st.sidebar.selectbox("종료 시간", time_index)

if st.sidebar.button("✅ 과목 추가"):
    if not course_name:
        st.sidebar.warning("과목명을 입력해주세요.")
    # 시작 시간이 종료 시간보다 늦으면 경고
    elif time_index.index(start_time_str) >= time_index.index(end_time_str):
        st.sidebar.error("종료 시간은 시작 시간보다 늦어야 합니다.")
    else:
        new_course = {
            'name': course_name,
            'day': selected_day,
            'start': start_time_str,
            'end': end_time_str
        }
        st.session_state.courses.append(new_course)
        st.sidebar.success(f"'{course_name}' 과목이 추가되었습니다.")

# 과목 삭제 기능
if st.session_state.courses:
    st.sidebar.markdown("---")
    st.sidebar.subheader("추가된 과목 목록")
    for i, course in enumerate(st.session_state.courses):
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        col1.write(f"**{course['name']}**: {course['day']} {course['start']} ~ {course['end']}")
        if col2.button("삭제", key=f"delete_{i}"):
            st.session_state.courses.pop(i)
            st.rerun() # 화면을 새로고침하여 즉시 반영

# --- 3. 시간표에 과목 표시 및 중복 검사 ---

# 중복 횟수를 기록하기 위한 DataFrame
overlap_df = pd.DataFrame(0, index=time_index, columns=days)

# session_state에 저장된 과목들을 시간표에 채우기
for course in st.session_state.courses:
    start_idx = time_index.index(course['start'])
    end_idx = time_index.index(course['end'])
    day = course['day']

    # 해당 과목의 시간대에 과목명과 중복 횟수 추가
    for i in range(start_idx, end_idx):
        time_label = time_index[i]
        
        # 이미 다른 과목이 있다면 줄바꿈으로 추가
        if schedule_df.loc[time_label, day]:
            schedule_df.loc[time_label, day] += f"\n{course['name']}"
        else:
            schedule_df.loc[time_label, day] = course['name']
        
        # 중복 횟수 1 증가
        overlap_df.loc[time_label, day] += 1

# --- 4. 시간표 스타일링 및 출력 ---

# 열(column) 전체에 스타일을 적용하는 함수
def style_column(col):
    # col.name은 현재 열의 이름 (예: '월')
    overlap_flags = overlap_df[col.name] > 1
    return ['background-color: #FF4B4B; color: white' if flag else '' for flag in overlap_flags]


# 스타일이 적용된 DataFrame 출력
st.markdown("### 🗓️ 나의 시간표")
st.dataframe(schedule_df.style.apply(style_column, axis=0), height=878)

st.info("ℹ️ 과목 시간이 겹치는 경우 해당 칸이 **빨간색**으로 표시됩니다.")
