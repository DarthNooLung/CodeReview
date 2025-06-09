from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os
import logging
import re

# ✅ 환경 변수 로드 및 초기 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
openai.api_key = api_key

# ✅ FastAPI 인스턴스 및 CORS 설정
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code-review-api")

# ✅ 확장자 → 언어 매핑
LANGUAGE_MAP = {
    'py': 'Python', 'java': 'Java', 'jsp': 'JSP', 'cs': 'C#', 'html': 'HTML',
    'js': 'JavaScript', 'ts': 'TypeScript', 'cpp': 'C++', 'c': 'C'
}

MAX_CHARS_PER_CHUNK = 4000  # 한 청크당 최대 문자 수


# ✅ 코드 청크 분할 함수
def split_into_chunks(code: str, chunk_size: int):
    return [code[i:i + chunk_size] for i in range(0, len(code), chunk_size)]


# ✅ 프롬프트 구성 함수
def build_chunk_prompt(code_chunk: str, ext: str, language: str, idx: int, total: int):
    return f"""
너는 숙련된 {language} 코드 리뷰어야. 아래는 전체 코드 파일의 {idx+1}/{total}번째 조각이야.
아래 코드를 리뷰해줘:
1. 기능 설명
2. 개선이 필요한 부분
3. 주요 변경 요약 (중요한 수정 또는 위험 요소에 주석 포함)
4. 리팩토링 코드

```{ext}
{code_chunk}
```
"""


# ✅ 리팩토링 코드 블럭 추출 함수
def extract_refactored_code(text: str) -> str:
    matches = re.findall(r"```[a-zA-Z]*\n([\s\S]*?)\n```", text)
    return matches[-1].strip() if matches else ""


# ✅ 메인 엔드포인트
@app.post("/review/")
async def review_code(
    file: UploadFile = File(...),
    model: str = Form("gpt-4")
):
    try:
        code = (await file.read()).decode("utf-8")
        ext = file.filename.split('.')[-1].lower()
        language = LANGUAGE_MAP.get(ext, "Plain Text")

        chunks = split_into_chunks(code, MAX_CHARS_PER_CHUNK)
        total = len(chunks)

        chunk_reviews = []
        final_refactor = ""

        for idx, chunk in enumerate(chunks):
            prompt = build_chunk_prompt(chunk, ext, language, idx, total)
            logger.info(f"▶ Chunk {idx+1}/{total} 요청 중... 모델: {model}")

            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            part_review = response.choices[0].message["content"]
            chunk_reviews.append({
                "chunk_index": idx,
                "markdown": part_review,
                "refactored_code": extract_refactored_code(part_review)
            })

            final_refactor = chunk_reviews[-1]["refactored_code"]

        return {
            "reviews": chunk_reviews,
            "final_refactored": final_refactor
        }

    except Exception as e:
        logger.error(f"[에러 발생] {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
