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

# ✅ 스마트 청크
def smart_chunking_html(code: str, chunk_size: int) -> list[str]:
    pattern = r'\n'
    parts = re.split(pattern, code)
    chunks = []
    buffer = ""
    for line in parts:
        if len(buffer) + len(line) < chunk_size:
            buffer += line + "\n"
        else:
            chunks.append(buffer)
            buffer = line + "\n"
    if buffer:
        chunks.append(buffer)
    return chunks

# ✅ 언어별 정렬 규칙
LANGUAGE_RULES = {
    "jsp": "- 들여쓰기는 탭으로 고정하세요.\n- html 구조를 변경하지 마세요.",
    "sql": "- 들여쓰기는 탭으로.\n- SELECT, FROM, JOIN 등은 줄바꿈.\n- 콤마는 줄 앞.",
    "java": "- 들여쓰기는 탭으로.\n- 중괄호는 같은 줄 유지.",
    "html": "- 구조 변경 없이 들여쓰기만 조정하세요. 들여쓰기는 탭 사용.",
    "python": "- 들여쓰기는 탭으로. 구조나 순서 변경 금지."
}

# ✅ 마크다운 제거
def extract_code_from_markdown(gpt_response: str) -> str:
    match = re.search(r"```[a-zA-Z]*\n([\s\S]*?)\n```", gpt_response)
    return match.group(1) if match else gpt_response

# 들여쓰기 구하는 함수
def count_indent_level(text: str, indent_char: str = "\t") -> int:
    lines = text.rstrip().splitlines()
    for line in reversed(lines):
        if line.strip() and line.startswith(indent_char):  # 비어있지 않고, 들여쓰기 있음
            return len(line) - len(line.lstrip(indent_char))
    return 0  # 기본값

# ✅ 새 후처리 함수: 줄 처음에만 2칸 스페이스 단위 → 탭 변환
def convert_2space_to_tab_only_at_line_start(line: str) -> str:
    return re.sub(r"^(  )+", lambda m: "\t" * (len(m.group(0)) // 2), line)

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

# ✅ GPT 기반 정렬 API
@app.post("/gpt_format/")
async def gpt_format_code(
    file: UploadFile = File(...),
    language: str = Form(...),
    model: str = Form("gpt-3.5-turbo")
):
    content = (await file.read()).decode("utf-8")

    additional_rule = "\n- 특히 들여쓰기는 반드시 '탭(tab)'으로 해 주세요. 절대 스페이스(공백)로 들여쓰지 마세요."
    additional_rule += "\n- 코드 외에 불필요한 설명, 주석, 메타 정보는 절대 추가하지 마세요. 원본에 없는 주석은 생성하지 마세요."

    rule = LANGUAGE_RULES.get(language.lower(), "\n- 들여쓰기 기준만 맞춰 정렬해 주세요.") + additional_rule

    if language.lower() in ["html", "jsp"]:
        chunks = smart_chunking_html(content, MAX_CHARS_PER_CHUNK)
    else:
        chunks = smart_chunking(content, MAX_CHARS_PER_CHUNK, LANGUAGE_MAP.get(language, "Plain Text"))

    formatted_blocks = []
    context_tail = ""

    for idx, chunk in enumerate(chunks):        
        indent_level = count_indent_level(context_tail)

        #print(f"이전 블록 탭 : {indent_level}")
        #print(f"[정렬 전 코드\\n{chunk}")

        prompt = (
            f"다음은 {language.upper()} 코드입니다.\n"
            f"{rule}\n"
            f"- 정렬 전 코드의 각 줄 들여쓰기(탭 개수)는 반드시 입력 그대로 보존해야 합니다.\n"
            f"- 들여쓰기는 오직 탭(tab)만 사용하고, 공백(스페이스)은 절대 사용하지 마세요.\n"
            f"- 줄마다 들여쓰기 깊이(탭 수)가 달라도 원본 코드의 계층 구조를 반드시 유지해야 합니다.\n"
            f"- 원본 구조, 태그, 계층, 줄 개수, 들여쓰기 단계를 임의로 바꾸거나 동일하게 맞추지 마세요.\n"
        )

        if context_tail:            
            prompt += (
                f"이전 코드 맥락 (들여쓰기 계층 유지를 위해 참고):\n"
                f"```{language.lower()}\n{context_tail}\n```\n\n"
            )

        prompt += (
            f"정렬 전 코드:\n"
            f"```{language.lower()}\n{chunk}\n```\n\n"
            f"정렬된 코드만 결과로 보여 주세요."
        )

        #print(f"idx : {idx+1}")
        #print(prompt)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            formatted = response.choices[0].message.content

            #print(f"[결과값 원본]\n{formatted}")

            formatted_code = extract_code_from_markdown(formatted)

            #print(f"[결과값 마크다운제거]\n{formatted_code}")

             # ✨ 적용: 줄 처음의 2칸 스페이스를 탭으로 변환
            lines = formatted_code.splitlines()
            corrected = [convert_2space_to_tab_only_at_line_start(line) for line in lines]
            formatted_code = "\n".join(corrected)

            formatted_blocks.append(formatted_code)

            CONTEXT_LINES = 30
            last_lines = formatted_code.rstrip().splitlines()[-CONTEXT_LINES:]
            context_tail = "\n".join(last_lines)

        except Exception as e:
            logger.error(f"[GPT 정렬 오류] Chunk {idx+1} 실패: {str(e)}")
            formatted_blocks.append(f"/* 오류: {str(e)} */")
            context_tail = ""
    
    #print("==== 청크 수:", len(formatted_blocks))
    #for i, chunk in enumerate(formatted_blocks):
        #print(f"[청크 {i+1}]:{chunk[:300]}...")

    final_code = "\n".join(formatted_blocks)
    return Response(content=final_code, media_type="text/plain")