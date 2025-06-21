
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from config import client, logger, LANGUAGE_MAP, MAX_CHARS_PER_CHUNK
from utils.chunk import smart_chunking
from utils.common import build_chunk_prompt, extract_refactored_code

router = APIRouter()

@router.post("/review/")
async def review_code(
    file: UploadFile = File(...),
    model: str = Form("gpt-3.5-turbo")
):
    try:
        code = (await file.read()).decode("utf-8")
        ext = file.filename.split('.')[-1].lower()
        language = LANGUAGE_MAP.get(ext, "Plain Text")

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
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": chunk_summary_prompt}],
                temperature=0.2
            )
            chunk_summary = response.choices[0].message.content.strip()
            chunk_summaries.append(chunk_summary)

        # 3. chunk별 요약으로 전체 요약 생성
        total_summary_prompt = f"""
아래는 대형 {language} 코드 파일을 여러 개 chunk로 나눠서 각 부분별로 요약한 내용이야.

각 chunk별 요약을 바탕으로 전체 코드의 구조와 기능을 통합적으로 요약해줘.
중복 없이 전체적인 흐름, 주요 역할, 핵심 구조 위주로 정리해줘.

{chr(10).join(chunk_summaries)}
"""
        summary_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": total_summary_prompt}],
            temperature=0.2
        )
        code_summary = summary_response.choices[0].message.content.strip()

        # 4. chunk별 코드 리뷰/리팩터
        chunk_reviews = []
        for idx, chunk in enumerate(chunks):
            prompt = build_chunk_prompt(chunk, ext, language, idx, total, code_summary)
            logger.info(f"▶ Chunk {idx+1}/{total} 리뷰 요청 중... 모델: {model}")
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
