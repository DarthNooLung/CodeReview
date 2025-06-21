from fastapi import APIRouter, UploadFile, File, Form, Response
from config import client, logger, LANGUAGE_RULES, LANGUAGE_MAP, MAX_CHARS_PER_CHUNK
from utils.chunk import smart_chunking, smart_chunking_html
from utils.common import extract_code_from_markdown, convert_2space_to_tab_only_at_line_start, count_indent_level

router = APIRouter()

@router.post("/gpt_format/")
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
                f"이 청크는 이전 코드 맥락(아래 코드 블록) 바로 뒤에 이어지는 부분입니다.\n"
                f"첫 줄의 들여쓰기를 반드시 이전 맥락의 마지막 줄과 동일하게 맞추고,\n"
                f"청크 내부의 계층(들여쓰기)는 절대로 임의로 변경하지 마세요.\n"
                f"들여쓰기는 반드시 탭(tab)만 사용하세요.\n"
                f"이전 코드 맥락:\n"
                f"이전 코드 맥락 (들여쓰기 계층 유지를 위해 참고):\n"
                f"```{language.lower()}\n{context_tail}\n```\n\n"
            )

        prompt += (
            f"정렬 전 코드:\n"
            f"```{language.lower()}\n{chunk}\n```\n\n"
            f"정렬된 코드만 결과로 보여 주세요."
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            formatted = response.choices[0].message.content
            formatted_code = extract_code_from_markdown(formatted)
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

    final_code = "\n".join(formatted_blocks)
    return Response(content=final_code, media_type="text/plain")