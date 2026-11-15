import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
from io import BytesIO
from PIL import Image

# --- 설정값 ---
BASE_URL = "https://www.kjbethel.kr/main/sub.html"
DOWNLOAD_DIR = "bulletin_images"
TOTAL_PAGES = 1  # 크롤링할 전체 페이지 수

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"[{directory}] 폴더가 생성되었습니다.")

def get_post_items(list_url):
    """게시판 목록 페이지에서 개별 글의 URL과 '실제 제목'을 함께 추출합니다."""
    response = requests.get(list_url, headers=HEADERS)
    response.encoding = 'utf-8'
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    post_items = []
    
    for a_tag in soup.find_all('a', href=True): 
        href = a_tag['href']
        if 'Mode=view' in href:
            full_url = urljoin(BASE_URL, href)
            # ★ a 태그 안에 있는 실제 게시글 제목(날짜) 텍스트를 가져옵니다.
            post_title = a_tag.text.strip()
            
            # 텍스트가 비어있지 않고, 중복된 URL이 아닐 경우에만 추가
            if post_title and not any(url == full_url for url, _ in post_items):
                post_items.append((full_url, post_title))
            
    return post_items

def download_images_from_post(post_url, post_title):
    """넘겨받은 실제 게시글 제목(post_title)을 파일명으로 사용해 이미지를 다운로드합니다.
       단, 크기가 너무 작은 장식용 이미지는 제외합니다."""
    response = requests.get(post_url, headers=HEADERS)
    response.encoding = 'utf-8'
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    safe_title = re.sub(r'[\\/:*?"<>|]', '', post_title).strip()
    
    content_area = soup.select_one('.board_content') 
    if not content_area:
        content_area = soup
        
    img_tags = content_area.find_all('img')
    img_count = 1
    
    for img in img_tags:
        img_url = img.get('src')
        if not img_url:
            continue
            
        img_full_url = urljoin(post_url, img_url)
        
        # 1차 필터링: 파일 이름으로 아이콘 등 명백한 장식 이미지 제외
        if img_url.endswith(('.gif', '.png')) and any(word in img_url.lower() for word in ['icon', 'btn', 'bg', 'bullet']):
            continue
            
        ext = os.path.splitext(img_url.split('/')[-1])[1]
        if not ext:
            ext = ".jpg"
            
        new_file_name = f"{safe_title}_{img_count}{ext}"
        file_path = os.path.join(DOWNLOAD_DIR, new_file_name)
        
        try:
            # 이미지를 메모리에 먼저 다운로드
            img_response = requests.get(img_full_url, headers=HEADERS)
            img_response.raise_for_status()
            img_data = img_response.content
            
            # 2차 필터링: Pillow 라이브러리로 실제 이미지 해상도(크기) 확인
            image_obj = Image.open(BytesIO(img_data))
            width, height = image_obj.size
            
            # 가로 또는 세로가 300 픽셀 미만인 아주 작은 이미지는 건너뜀 (수치 조절 가능)
            if width < 300 or height < 300:
                print(f"  -> 작아서 제외됨: {img_full_url.split('/')[-1]} ({width}x{height})")
                continue
            
            # 크기 조건을 통과한 실제 주보 이미지만 파일로 저장
            with open(file_path, 'wb') as f:
                f.write(img_data)
            print(f"  -> 다운로드 완료: {new_file_name} ({width}x{height})")
            img_count += 1
            
        except Exception as e:
            print(f"  -> 다운로드 실패 ({img_full_url}): {e}")
def main():
    create_directory(DOWNLOAD_DIR)
    print("=== 광주베델교회 주보 이미지 대량 다운로드를 시작합니다 ===")
    
    for page in range(1, TOTAL_PAGES + 1):
        list_url = f"https://www.kjbethel.kr/main/sub.html?Mode=list&boardID=www49&page={page}"
        print(f"\n[ {page} 페이지 ] 탐색 중...")
        
        post_items = get_post_items(list_url)
        print(f"  - 발견된 게시물 수: {len(post_items)}개")
        
        # URL과 제목을 같이 넘겨줍니다.
        for link, title in post_items:
            download_images_from_post(link, title)
            
        time.sleep(2)
        
    print("\n=== 모든 주보 이미지 다운로드가 성공적으로 완료되었습니다! ===")

if __name__ == "__main__":
    main()