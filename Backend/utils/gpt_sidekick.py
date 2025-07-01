import os
import openai
import asyncio
from config import client
from openai import AsyncOpenAI

def ask_sidekick(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
    system_prompt: str = "당신은 유용한 AI 어시스턴트입니다."
) -> str:
    """
    GPT 사이드킥에게 프롬프트를 보내 응답을 받습니다.

    Args:
        prompt (str): 사용자 질문 또는 요청
        model (str): 사용할 GPT 모델 이름
        temperature (float): 창의성 온도 (기본 0.2)
        system_prompt (str): 시스템 역할 메시지 (컨텍스트 설정)

    Returns:
        str: GPT의 응답 텍스트
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[Sidekick Error] GPT 요청 실패: {e}")
        return ""


def format_finding_with_gpt(finding: str, model: str = "gpt-3.5-turbo") -> str:
    #client = AsyncOpenAI()

    """
    단일 finding(문자열)에 대해 GPT에게 개선 피드백을 요청하는 함수
    """
    prompt = (
        "아래 정적 분석 결과([Finding])를 참고해서 다음을 수행해 주세요.\n"
        "1. 해당 문제를 초보 개발자도 이해할 수 있게 설명해 주세요.\n"
        "2. 문제를 수정하는 구체적인 방법을 제안해 주세요.\n"
        "3. 참고할 수 있는 개선된 코드 예제도 함께 제공해 주세요.\n\n"
        f"[Finding]\n{finding}"
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 숙련된 소프트웨어 보안 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return completion.choices[0].message.content.strip()


def format_findings_with_gpt_bulk(findings: list[str], model: str = "gpt-4o") -> list[str]:
    """
    여러 finding 항목을 받아서 각 항목별 GPT 피드백을 병렬로 생성
    기존 format_finding_with_gpt()를 그대로 활용
    """
    tasks = [format_finding_with_gpt(f, model) for f in findings]
    results = asyncio.gather(*tasks)
    return results