@echo off
chcp 65001
cd /d "%~dp0"

echo === 1. 최신 주보 다운로드 ===
py image.py

echo === 2. 구글 비전 OCR 추출 ===
py ocr_extract.py

echo === 3. 웹사이트(클라우드)로 자동 반영 ===
git add .
git commit -m "매주 주보 자동 업데이트"
git push origin main

echo === 업데이트가 완료되었습니다! 5초 뒤 창이 닫힙니다. ===
timeout /t 5