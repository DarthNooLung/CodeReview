import re
from typing import Callable

# 간단한 인메모리 캐시 (서버 재시작하면 초기화됨)
_feedback_cache = {}


def normalize_finding_message(summary: str) -> str:
    """
    주어진 Semgrep finding summary에서 라인 번호 등 가변 요소를 제거해
    동일 오류를 동일 키로 캐싱할 수 있도록 정규화.

    예:
        '[rule123] path/to/file.jsp:45 - 위험한 함수'
        → '[rule123] - 위험한 함수'
    """
    # :숫자 - 부분을 ' - '로 치환
    return re.sub(r':\d+\s*-\s*', ' - ', summary)


def get_gpt_feedback_cached(
    summary: str,
    gpt_model: str,
    gpt_call_func: Callable[[str, str], str]
) -> str:
    """
    GPT 호출을 캐싱해 동일 메시지에 대해 GPT 재호출을 방지.

    Parameters:
        summary (str): 원본 Semgrep finding summary
        gpt_model (str): 사용할 GPT 모델명
        gpt_call_func (Callable): GPT 호출 함수 (prompt, model) -> str

    Returns:
        str: GPT가 생성한 피드백
    """
    normalized_key = normalize_finding_message(summary)

    # 캐시에 있으면 재사용
    if normalized_key in _feedback_cache:
        return _feedback_cache[normalized_key]

    # GPT 호출
    feedback = gpt_call_func(summary, gpt_model)

    # 캐시에 저장
    _feedback_cache[normalized_key] = feedback
    return feedback


def clear_cache():
    """
    캐시를 수동으로 비울 때 사용
    """
    _feedback_cache.clear()


def cache_size() -> int:
    """
    현재 캐시된 항목 개수
    """
    return len(_feedback_cache)
