import re
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from config import client, logger, LANGUAGE_MAP, MAX_CHARS_PER_CHUNK
from utils.chunk import smart_chunking
from utils.common import build_chunk_prompt, extract_refactored_code
from utils.security import allowed_file, file_size_okay
from utils.sast import semgrep_scan_code
from utils.mask_utils import mask_all_sensitive_in_result
from utils.split_utils import split_jsp, split_aspx, split_html
from utils.gpt_sidekick import ask_sidekick

router = APIRouter()

def format_review_output(raw_result: dict) -> str:
    output = []

    # [정적 분석 결과]
    output.append("🔍 [정적 분석 결과]")
    output.append(raw_result.get("sast_result", "").strip())

    # [전체 요약]
    output.append("\n🧩 [전체 코드 요약]")
    output.append(raw_result.get("summary", "").strip())

    # [리뷰 섹션]
    output.append("\n🧠 [코드 리뷰]")
    for review in raw_result.get("reviews", []):
        index = review["chunk_index"] + 1
        markdown = review.get("markdown", "").strip()
        refactor = review.get("refactored_code", "").strip()

        output.append(f"\n--- ⬛ Chunk {index} ⬛ ---")

        # 리뷰 분석 블록
        if "기능 설명:" in markdown or "개선이 필요한 부분:" in markdown:
            # 이미 구분돼 있는 경우
            output.append(markdown)
        else:
            output.append("리뷰:\n" + markdown)

        # 리팩토링 코드 별도 구분
        if refactor:
            output.append("\n리팩토링 코드:\n" + refactor)

    # 최종 통합 리팩토링 코드
    final = raw_result.get("final_refactored", "").strip()
    if final:
        output.append("\n✅ [최종 리팩토링 코드 통합]")
        output.append(final)

    return "\n\n".join(output)



@router.post("/review/")
async def review_code(
    file: UploadFile = File(...),
    model: str = Form("gpt-3.5-turbo")
):
    try:
        if not allowed_file(file.filename):
            return JSONResponse(status_code=400, content={"error": "허용되지 않는 확장자입니다."})

        content = await file.read()
        if not file_size_okay(content):
            return JSONResponse(status_code=400, content={"error": "파일 용량이 너무 큽니다."})
            
        code = content.decode("utf-8")
        ext = file.filename.split('.')[-1].lower()
        language = LANGUAGE_MAP.get(ext, "Plain Text")

        logger.info(f"정적분석 시작 : {file.filename}")

        # JSP/ASPX 분리 분석 분기
        sast_result = ""
        if ext == "jsp":
            # html, java, js, css 분리
            html_part, java_part, js_part, css_part = split_jsp(code)
            sast_html = semgrep_scan_code(html_part, 'html')
            sast_java = semgrep_scan_code(java_part, 'java') if java_part.strip() else "[Java 코드 없음]"
            sast_js = semgrep_scan_code(js_part, 'js') if js_part.strip() else "[JS 코드 없음]"
            sast_css = semgrep_scan_code(css_part, 'css') if css_part.strip() else "[CSS 코드 없음]"
            sast_result = (
                f"[HTML 분석]\n{sast_html}\n\n"
                f"[Java 분석]\n{sast_java}\n\n"
                f"[JS 분석]\n{sast_js}\n\n"
                f"[CSS 분석]\n{sast_css}"
            )

        elif ext == "aspx":
            # html, cs, js, css 분리
            html_part, cs_part, js_part, css_part = split_aspx(code)
            sast_html = semgrep_scan_code(html_part, 'html')
            sast_cs = semgrep_scan_code(cs_part, 'cs') if cs_part.strip() else "[C# 코드 없음]"
            sast_js = semgrep_scan_code(js_part, 'js') if js_part.strip() else "[JS 코드 없음]"
            sast_css = semgrep_scan_code(css_part, 'css') if css_part.strip() else "[CSS 코드 없음]"
            sast_result = (
                f"[HTML 분석]\n{sast_html}\n\n"
                f"[C# 분석]\n{sast_cs}\n\n"
                f"[JS 분석]\n{sast_js}\n\n"
                f"[CSS 분석]\n{sast_css}"
            )
        elif ext in ["java", "js", "html", "py", "cs", "css"]:
            sast_result = semgrep_scan_code(code, ext)
        elif ext == "html":
            html_only, js_code, css_code = split_html(code)
            sast_html = semgrep_scan_code(html_only, 'html')
            sast_js = semgrep_scan_code(js_code, 'js') if js_code.strip() else "[JS 코드 없음]"
            sast_css = semgrep_scan_code(css_code, 'css') if css_code.strip() else "[CSS 코드 없음]"
            sast_result = (
                f"[HTML 분석]\n{sast_html}\n\n"
                f"[JS 분석]\n{sast_js}\n\n"
                f"[CSS 분석]\n{sast_css}"
            )
        else:
            sast_result = "[지원되지 않는 파일 유형이거나 SAST 분석 불가]"

        #print(f"[정적분석(분리 결과)]\n{sast_result}")
        
        # 1. 코드 chunk 분할
        chunks = smart_chunking(code, MAX_CHARS_PER_CHUNK, language)
        total = len(chunks)
        
        # 2. 각 chunk별 요약
        chunk_summaries = []
        
        for idx, chunk in enumerate(chunks):
            chunk_summary_prompt = f"""
아래는 전체 {language} 코드의 일부야. 이 부분의 구조와 주요 기능을 간단히 요약해줘.

[코드 시작]
{chunk}
[코드 끝]
"""
            logger.info(f"▶ Chunk {idx+1}/{total} 요약 요청 중... 모델: {model}")
            chunk_summary = ask_sidekick(chunk_summary_prompt, model, 0.2)
            chunk_summaries.append(chunk_summary)

        # 3. chunk별 요약으로 전체 요약 생성
        total_summary_prompt = f"""
아래는 대형 {language} 코드 파일을 여러 개 chunk로 나눠서 각 부분별로 요약한 내용이야.

[정적분석(분리 결과)]
{sast_result}

각 chunk별 요약을 바탕으로 전체 코드의 구조와 기능을 통합적으로 요약해줘.
중복 없이 전체적인 흐름, 주요 역할, 핵심 구조 위주로 정리해줘.

{chr(10).join(chunk_summaries)}
"""
        code_summary = ask_sidekick(total_summary_prompt, model, 0.2)

        # 4. chunk별 코드 리뷰/리팩터
        chunk_reviews = []
        for idx, chunk in enumerate(chunks):
            prompt = build_chunk_prompt(chunk, ext, language, idx, total, code_summary)
            logger.info(f"▶ Chunk {idx+1}/{total} 리뷰 요청 중... 모델: {model}")
            
            part_review = ask_sidekick(prompt, model, 0.2)

            chunk_reviews.append({
                "chunk_index": idx,
                "markdown": part_review,
                "refactored_code": extract_refactored_code(part_review)
            })

        final_refactor = "\n".join([r["refactored_code"] for r in chunk_reviews if r["refactored_code"]])

        raw_result = {
            "sast_result": sast_result,
            "summary": code_summary,
            "reviews": chunk_reviews,
            "final_refactored": final_refactor
        }
        
        return raw_result
        #return mask_all_sensitive_in_result(raw_result)

    except Exception as e:
        logger.error(f"[에러 발생] {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
