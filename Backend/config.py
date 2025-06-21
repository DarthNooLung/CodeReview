import os
import openai
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

openai.api_key = api_key

client = openai.OpenAI(
    api_key=api_key,
    http_client=httpx.Client(verify=False)
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code-review-api")

LANGUAGE_MAP = {
    'py': 'Python', 'java': 'Java', 'jsp': 'JSP', 'cs': 'C#', 'html': 'HTML',
    'js': 'JavaScript', 'ts': 'TypeScript', 'cpp': 'C++', 'c': 'C', 'vue': 'Vue',
    'sql': 'SQL'
}
LANGUAGE_RULES = {
    "jsp": "- 들여쓰기는 탭으로 고정하세요.\n- html 구조를 변경하지 마세요.",
    "sql": "- 들여쓰기는 탭으로.\n- SELECT, FROM, JOIN 등은 줄바꿈.\n- 콤마는 줄 앞.",
    "java": "- 들여쓰기는 탭으로.\n- 중괄호는 같은 줄 유지.",
    "html": "- 구조 변경 없이 들여쓰기만 조정하세요. 들여쓰기는 탭 사용.",
    "python": "- 들여쓰기는 탭으로. 구조나 순서 변경 금지."
}
MAX_CHARS_PER_CHUNK = 10000