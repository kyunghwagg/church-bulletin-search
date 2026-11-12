import streamlit as st
import pandas as pd
import os
from PIL import Image

# 1. 웹페이지 기본 설정 (브라우저 탭 이름, 넓은 화면 사용)
st.set_page_config(page_title="주보 통합 검색", page_icon="💒", layout="wide")

# 데이터 로딩 함수 (속도 향상을 위해 한 번만 읽고 메모리에 저장)
@st.cache_data
def load_data():
    try:
        return pd.read_excel("주보_텍스트_추출결과.xlsx")
    except FileNotFoundError:
        return None

df = load_data()

st.title("💒 광주베델교회 주보 검색 시스템")
st.markdown("---")

if df is None:
    st.error("🚨 '주보_텍스트_추출결과.xlsx' 파일을 찾을 수 없습니다. OCR 추출 작업을 먼저 완료해 주세요.")
else:
    # 2. 검색창 인터페이스 구현
    search_keyword = st.text_input("🔍 검색할 단어를 입력하세요 (예: 교인 이름, 설교 제목, 직분)", "")

    if search_keyword:
        # 3. 검색어가 포함된 데이터 필터링
        # 결측치를 무시하고(na=False), 검색어가 포함된(contains) 데이터만 추출
        mask = df['추출된 텍스트'].astype(str).str.contains(search_keyword, case=False, na=False)
        search_results = df[mask]

        st.subheader(f"총 {len(search_results)}건의 주보에서 '{search_keyword}'(을)를 찾았습니다.")
        
        # 4. 검색 결과 화면 출력
        for index, row in search_results.iterrows():
            file_name = row['파일명']
            text_content = str(row['추출된 텍스트'])
            
            # 파일명에서 확장자를 제거하여 깔끔한 제목으로 표시 (예: "2026년 11월 8일 주보_1")
            clean_title = os.path.splitext(file_name)[0]
            
            # 접기/펴기 기능(expander)을 사용해 화면을 깔끔하게 유지
            with st.expander(f"📄 {clean_title}"):
                # 화면을 좌우 두 칸으로 나누기
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### 📝 추출된 텍스트")
                    # 검색어 부분에 노란색 형광펜 효과(마크다운 HTML) 적용
                    highlighted_text = text_content.replace(
                        search_keyword, 
                        f"<span style='background-color: yellow; font-weight: bold; color: black;'>{search_keyword}</span>"
                    )
                    # 원본 텍스트의 줄바꿈을 웹에서도 유지하도록 <br>로 치환
                    highlighted_text = highlighted_text.replace("\n", "<br>")
                    st.markdown(highlighted_text, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### 🖼️ 원본 이미지")
                    image_path = os.path.join("bulletin_images", file_name)
                    if os.path.exists(image_path):
                        # 이미지를 해당 단의 너비에 딱 맞게 표시
                        st.image(image_path, use_container_width=True)
                    else:
                        st.info("원본 이미지 파일을 찾을 수 없습니다.")