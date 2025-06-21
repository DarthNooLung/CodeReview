import re

def extract_code_from_markdown(gpt_response: str) -> str:
    match = re.search(r"```[a-zA-Z]*\n([\s\S]*?)\n```", gpt_response)
    return match.group(1) if match else gpt_response

def count_indent_level(text: str, indent_char: str = "\t") -> int:
    lines = text.rstrip().splitlines()
    for line in reversed(lines):
        if line.strip() and line.startswith(indent_char):
            return len(line) - len(line.lstrip(indent_char))
    return 0

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