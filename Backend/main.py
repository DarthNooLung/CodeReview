from fastapi import Response

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os
import logging
import re
import httpx

# ✅ 환경 변수 로드 및 초기 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
openai.api_key = api_key

client = openai.OpenAI(
    api_key=api_key,
    http_client=httpx.Client(verify=False)
)

# ✅ FastAPI 인스턴스 및 CORS 설정
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
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
    'js': 'JavaScript', 'ts': 'TypeScript', 'cpp': 'C++', 'c': 'C', 'vue': 'Vue',
    'sql': 'SQL'
}

MAX_CHARS_PER_CHUNK = 10000

@app.post("/format/")
async def format_code(
    file: UploadFile = File(...),
    indent: str = Form("4"),
    brace: str = Form("same-line"),
    comma: str = Form("leading")
):
    code = (await file.read()).decode("utf-8")
    ext = file.filename.split(".")[-1].lower()

    def get_indent() -> str:
        if indent == "tab":
            return "\t"
        return " " * int(indent)

    def format_sql_extended(code: str) -> str:
        lines = code.splitlines()
        formatted = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith(("SELECT", "FROM", "WHERE", "JOIN", "ON", "AND", "OR", "GROUP BY", "ORDER BY")):
                formatted.append("\n" + line)
            elif comma == "leading" and line.startswith(","):
                formatted.append("\n" + line)
            elif comma == "trailing" and line.endswith(","):
                formatted.append(line)
            else:
                formatted.append(get_indent() + line)
        return "\n".join(formatted)

    def format_block_style_extended(code: str) -> str:
        lines = code.splitlines()
        formatted = []
        level = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("}") or stripped.startswith(");") or stripped.startswith("end"):
                level = max(0, level - 1)
            prefix = get_indent() * level
            if brace == "next-line" and "{" in stripped and not stripped.startswith("{"):
                parts = stripped.split("{")
                formatted.append(prefix + parts[0].strip())
                formatted.append(prefix + "{")
            else:
                formatted.append(prefix + stripped)
            if stripped.endswith("{") or stripped.endswith("(") or stripped.endswith("then") or (
                "{" in stripped and "}" not in stripped):
                level += 1
            elif stripped.endswith("begin"):
                level += 1
        return "\n".join(formatted)

    def format_html(code: str) -> str:
        import re
        code = re.sub(r'>\s*<', '>\n<', code)
        return format_block_style_extended(code)

    if ext == "sql":
        result = format_sql_extended(code)
    elif ext in ("java", "js", "ts", "py", "c", "cpp"):
        result = format_block_style_extended(code)
    elif ext in ("jsp", "html"):
        result = format_html(code)
    else:
        result = format_block_style_extended(code)

    return {"formatted": result}

# 기존 GPT 기반 리뷰 API 유지
def smart_chunking(code: str, chunk_size: int, language: str = "Plain Text") -> list[str]:
    lang_patterns = {
        "Python": r'(\n(?:def|class)\s+\w+.*?:)',
        "Java": r'(\n\s*(public|private|protected)?\s*(static)?\s*(class|interface|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
        "C#": r'(\n\s*(public|private|protected)?\s*(static)?\s*(class|interface|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
        "JavaScript": r'(\n\s*(function|class)\s+\w+\s*\([^)]*\)\s*\{)',
        "TypeScript": r'(\n\s*(function|class)\s+\w+\s*\([^)]*\)\s*\{)',
        "C++": r'(\n\s*(class|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
    }
    pattern = lang_patterns.get(language, r'\n')
    parts = re.split(pattern, code)
    chunks = []
    buffer = ""
    i = 0
    while i < len(parts):
        unit = parts[i]
        if i + 1 < len(parts):
            unit += parts[i + 1]
            i += 2
        else:
            i += 1
        if len(buffer) + len(unit) < chunk_size:
            buffer += unit
        else:
            if buffer:
                chunks.append(buffer)
            buffer = unit
    if buffer:
        chunks.append(buffer)
    return chunks

def build_chunk_prompt(code_chunk: str, ext: str, language: str, idx: int, total: int, summary: str):
    return f"""
너는 숙련된 {language} 코드 리뷰어야. 아래는 전체 코드 파일의 {idx+1}/{total}번째 조각이야.

전체 코드 요약:
{summary}

이 조각의 코드를 리뷰해줘:
1. 기능 설명
2. 개선이 필요한 부분 (특히 보안적으로 문제가 있는지 점검)
3. 주요 변경 요약 (중요한 수정 또는 위험 요소에 주석 포함)
4. 리팩토링 코드

```{ext}
{code_chunk}
```
"""

def extract_refactored_code(text: str) -> str:
    matches = re.findall(r"```[a-zA-Z]*\n([\s\S]*?)\n```", text)
    return matches[-1].strip() if matches else ""

@app.post("/review/")
async def review_code(
    file: UploadFile = File(...),
    model: str = Form("gpt-3.5-turbo")
):
    try:
        code = (await file.read()).decode("utf-8")
        ext = file.filename.split('.')[-1].lower()
        language = LANGUAGE_MAP.get(ext, "Plain Text")

        summary_prompt = f"""
다음은 전체 {language} 코드야. 전체 구조와 기능을 요약해줘:
```{ext}
{code}
```
"""
        summary_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2
        )
        code_summary = summary_response.choices[0].message.content

        chunks = smart_chunking(code, MAX_CHARS_PER_CHUNK, language)
        total = len(chunks)

        chunk_reviews = []

        for idx, chunk in enumerate(chunks):
            prompt = build_chunk_prompt(chunk, ext, language, idx, total, code_summary)
            logger.info(f"▶ Chunk {idx+1}/{total} 요청 중... 모델: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            part_review = response.choices[0].message.content
            chunk_reviews.append({
                "chunk_index": idx,
                "markdown": part_review,
                "refactored_code": extract_refactored_code(part_review)
            })

        final_refactor = "\n".join([r["refactored_code"] for r in chunk_reviews if r["refactored_code"]])

        return {
            "summary": code_summary,
            "reviews": chunk_reviews,
            "final_refactored": final_refactor
        }

    except Exception as e:
        logger.error(f"[에러 발생] {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/gpt_format/")
async def gpt_format_code(
    file: UploadFile = File(...),
    language: str = Form(...),
    model: str = Form("gpt-3.5-turbo"),  # ✅ 추가: gpt-3.5-turbo, gpt-4, gpt-4o 등
    style: str = Form("깔끔하고 정돈된 코드 스타일로 정렬해줘")
):
    content = (await file.read()).decode("utf-8")

    prompt = f"""
다음은 {language.upper()} 코드입니다. 다음 기준에 따라 보기 좋게 정렬해 주세요:

- 들여쓰기: 탭 문자
- 콤마 위치: 줄 앞에 오도록 (leading comma)
- 중괄호 또는 서브쿼리 들여쓰기를 계층적으로 정렬
- 정렬 전 코드:
```{language.lower()}
{content}
```

정렬 후 코드만 결과로 보여 주세요.
"""

    try:
        response = client.chat.completions.create(
            model=model,  # ✅ 선택된 모델 사용
            messages=[{ "role": "user", "content": prompt }],
            temperature=0.3
        )
        formatted = response.choices[0].message.content
        # print(formatted)
        return Response(content=formatted, media_type="text/plain")

    except Exception as e:
        logger.error(f"[GPT 정렬 오류] {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
