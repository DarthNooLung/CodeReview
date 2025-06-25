import os
import openai
from config import client

def ask_sidekick(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.2) -> str:
    """
    GPT 사이드킥에게 프롬프트를 보내 응답을 받습니다.

    Args:
        prompt (str): 사용자 질문 또는 요청
        model (str): 사용할 GPT 모델 이름
        temperature (float): 창의성 온도 (기본 0.2)

    Returns:
        str: GPT의 응답 텍스트
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[Sidekick Error] GPT 요청 실패: {e}")
        return ""