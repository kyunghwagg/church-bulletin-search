import os
import io
import pandas as pd
from google.cloud import vision

IMAGE_DIR = "bulletin_images"
KEY_PATH = "vision_key.json"
OUTPUT_FILE = "주보_텍스트_추출결과.xlsx"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

def extract_text_from_image(client, image_path):
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"{response.error.message}")
    
    texts = response.text_annotations
    return texts[0].description if texts else ""

def main():
    client = vision.ImageAnnotatorClient()
    
    # 기존 엑셀 파일이 있으면 읽어오고, 없으면 빈 데이터프레임 생성
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_excel(OUTPUT_FILE)
        # 이미 처리된 파일명 목록 확보
        processed_files = existing_df['파일명'].tolist()
    else:
        existing_df = pd.DataFrame(columns=["파일명", "추출된 텍스트"])
        processed_files = []

    all_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    # 전체 파일 중 '기존 엑셀에 없는(새로 다운로드된)' 파일만 추려냄
    new_files = [f for f in all_files if f not in processed_files]
    
    if not new_files:
        print("새로 추가된 주보 이미지가 없습니다. 업데이트를 종료합니다.")
        return

    print(f"총 {len(new_files)}개의 새로운 주보 이미지에서 텍스트를 추출합니다.\n")
    new_results = []

    for idx, file_name in enumerate(new_files, start=1):
        image_path = os.path.join(IMAGE_DIR, file_name)
        print(f"[{idx}/{len(new_files)}] 추출 중: {file_name} ...", end=" ")
        
        try:
            extracted_text = extract_text_from_image(client, image_path)
            new_results.append({
                "파일명": file_name,
                "추출된 텍스트": extracted_text
            })
            print("완료")
        except Exception as e:
            print(f"실패 ({e})")

    # 새로 추출한 데이터를 기존 데이터 밑에 합쳐서 엑셀 덮어쓰기
    if new_results:
        new_df = pd.DataFrame(new_results)
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
        final_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\n=== 업데이트 완료! 총 {len(final_df)}건의 데이터가 엑셀에 저장되었습니다 ===")

if __name__ == "__main__":
    main()