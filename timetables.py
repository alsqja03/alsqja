import streamlit as st
import pandas as pd
from datetime import time, timedelta
import hashlib

# --- 1. 기본 설정 및 데이터 구조 생성 ---

st.set_page_config(layout="wide")
st.title("🎨 수강신청 시간표 도우미 (셀 병합 & 색상)")

# session_state 초기화
if 'courses' not in st.session_state:
    st.session_state.courses = []

# --- 색상 팔레트 ---
# 각 과목에 고유한 색상을 할당하기 위한 리스트
# (색상 출처: https://coolors.co/)
COLOR_PALETTE = [
    "#F94144", "#F3722C", "#F8961E", "#F9C74F", "#90BE6D",
    "#43AA8B", "#4D908E", "#577590", "#277DA1", "#003049"
]

# 과목명에 따라 고유한 색상을 결정하는 함수
def get_color_for_course(course_name):
    # 과목명을 해싱하여 0-9 사이의 숫자로 변환 -> 팔레트 인덱스로 사용
    hash_object = hashlib.md5(course_name.encode())
    hex_hash = hash_object.hexdigest()
    index = int(hex_hash, 16) % len(COLOR_PALETTE)
    return COLOR_PALETTE[index]

# 시간표의 시간 인덱스 생성
time_index = []
current_time = time(8, 0)
end_time = time(19, 30)
while current_time <= end_time:
    time_str = current_time.strftime('%H:%M')
    if current_time.minute == 0:
        class_period = current_time.hour - 8
        label = f"{class_period} ({time_str})"
    else:
        label = f".5 ({time_str})"
    time_index.append(label)
    current_time = (pd.to_datetime(f'2024-01-01 {current_time}') + timedelta(minutes=30)).time()

days = ['월', '화', '수', '목', '금', '토', '일']

# --- 2. 사용자 입력 (사이드바) ---

st.sidebar.header("과목 추가하기")
course_name = st.sidebar.text_input("과목명", placeholder="예: 파이썬 기초")
selected_day = st.sidebar.selectbox("요일", days)
start_time_str = st.sidebar.selectbox("시작 시간", time_index)
end_time_str = st.sidebar.selectbox("종료 시간", time_index)

if st.sidebar.button("✅ 과목 추가"):
    if not course_name:
        st.sidebar.warning("과목명을 입력해주세요.")
    elif time_index.index(start_time_str) >= time_index.index(end_time_str):
        st.sidebar.error("종료 시간은 시작 시간보다 늦어야 합니다.")
    else:
        new_course = {
            'name': course_name,
            'day': selected_day,
            'start': start_time_str,
            'end': end_time_str,
            'color': get_color_for_course(course_name) # 과목별 색상 할당
        }
        st.session_state.courses.append(new_course)
        st.sidebar.success(f"'{course_name}' 과목이 추가되었습니다.")
        st.rerun()

if st.session_state.courses:
    st.sidebar.markdown("---")
    st.sidebar.subheader("추가된 과목 목록")
    for i, course in enumerate(st.session_state.courses):
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        col1.write(f"**{course['name']}**: {course['day']} {course['start']} ~ {course['end']}")
        if col2.button("삭제", key=f"delete_{i}"):
            st.session_state.courses.pop(i)
            st.rerun()

# --- 3. HTML 시간표 생성 ---

# 시간표 데이터를 저장할 2차원 리스트 (dict)
schedule_data = [[[] for _ in days] for _ in time_index]

# 과목 정보를 schedule_data에 채우기
for course in st.session_state.courses:
    start_idx = time_index.index(course['start'])
    end_idx = time_index.index(course['end'])
    day_idx = days.index(course['day'])
    duration = end_idx - start_idx

    # 과목 정보를 시작 시간에만 저장 (rowspan 정보 포함)
    schedule_data[start_idx][day_idx].append({
        'name': course['name'],
        'duration': duration,
        'color': course['color']
    })
    
    # 나머지 시간은 'occupied'로 표시하여 셀을 그리지 않도록 함
    for i in range(start_idx + 1, end_idx):
        schedule_data[i][day_idx].append({'name': 'occupied'})

# HTML 테이블 생성
html = """
<style>
    .timetable {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }
    .timetable th, .timetable td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: center;
        height: 35px; /* 셀 높이 고정 */
        font-size: 14px;
        color: white; /* 기본 텍스트 색상 */
    }
    .timetable th {
        background-color: #333;
    }
    .timetable .time-label {
        background-color: #444;
        width: 100px; /* 시간 열 너비 고정 */
        font-weight: bold;
    }
    .overlap {
        background-color: #D32F2F !important; /* 중복 시 배경색 (중요도 높임) */
        font-weight: bold;
    }
</style>
<table class="timetable">
    <thead>
        <tr>
            <th>시간</th>
"""
for day in days:
    html += f"<th>{day}</th>"
html += "</tr></thead><tbody>"

for i, time_label in enumerate(time_index):
    html += "<tr>"
    html += f"<td class='time-label'>{time_label}</td>"
    for j, day in enumerate(days):
        cell_content = schedule_data[i][j]
        
        # 'occupied'는 이미 rowspan으로 처리되었으므로 건너뜀
        if any(c.get('name') == 'occupied' for c in cell_content):
            continue

        # 셀에 내용이 있는 경우
        if cell_content:
            # 시간이 겹치는 경우 (한 셀에 2개 이상 과목)
            if len(cell_content) > 1:
                class_names = "<br>".join([c['name'] for c in cell_content])
                html += f"<td class='overlap'>{class_names}</td>"
            # 과목이 하나만 있는 경우
            else:
                course_info = cell_content[0]
                duration = course_info['duration']
                color = course_info['color']
                html += f"<td rowspan={duration} style='background-color: {color}; vertical-align: middle;'>{course_info['name']}</td>"
        # 빈 셀인 경우
        else:
            html += "<td></td>"
    html += "</tr>"

html += "</tbody></table>"

# --- 4. 시간표 출력 ---
st.markdown("### 🗓️ 나의 시간표")
st.markdown(html, unsafe_allow_html=True)
st.info("ℹ️ 과목 시간이 겹치는 경우 해당 칸이 **빨간색**으로 표시됩니다.")
