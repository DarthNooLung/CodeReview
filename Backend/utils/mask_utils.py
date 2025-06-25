import re

# 주요 민감정보 패턴 (회사 정책/특성에 맞게 추가 가능)
MASK_KEYS = [
    r'password',
    r'passwd',
    r'secret',
    r'api[_\-]?key',
    r'access[_\-]?token',
    r'client[_\-]?secret',
    r'private[_\-]?key',
    r'db[_\-]?url',
    r'db[_\-]?user',
    r'db[_\-]?pass',
    r'aws[_\-]?access',
    r'aws[_\-]?secret',
    r'encrypt(ion)?[_\-]?key',
    r'jwt[_\-]?secret',
    r'oauth[_\-]?token',
    r'slack[_\-]?token',
    r'mail[_\-]?pass',
    r'email',
    r'phone',
    r'phonenumber',
    r'전화번호',
    r'이메일'
]

# 마스킹 방식: 실제 값 길이 유지(*****) 또는 항상 고정 ****
def mask_sensitive(text: str, mask: str = "****") -> str:
    # 각 키워드가 포함된 라인의 값만 마스킹
    for key in MASK_KEYS:
        # password = 'xxx' 또는 password: 'xxx'
        pattern = rf'({key}\s*[=:]\s*)([\"\']?)[^\"\',;\n]+([\"\']?)'
        text = re.sub(pattern, rf'\1{mask}\3', text, flags=re.IGNORECASE)
        # "password": "xxx" (JSON 스타일)
        pattern2 = rf'(\"{key}\"\s*:\s*\")[^\"\']+(\"?)'
        text = re.sub(pattern2, rf'\1{mask}\2', text, flags=re.IGNORECASE)
        # 이메일 마스킹: 중간 *처리
        if key in ["email", "이메일"]:
            email_pattern = r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
            text = re.sub(email_pattern, lambda m: m.group(1)[0] + "****@" + m.group(2), text)
        # 전화번호 마스킹 (국내/해외)
        if key in ["phone", "phonenumber", "전화번호"]:
            phone_pattern = r'(01[016789]{1}|02|0[3-9]{1}[0-9]{1})-?\d{3,4}-?\d{4}'
            text = re.sub(phone_pattern, lambda m: m.group(0)[:3] + "-****-" + m.group(0)[-4:], text)
    return text

# 파일 단위로 한번에 마스킹하는 헬퍼
def mask_all_sensitive_in_result(result_dict: dict, mask: str = "****") -> dict:
    new_result = {}
    for k, v in result_dict.items():
        if isinstance(v, str):
            new_result[k] = mask_sensitive(v, mask)
        elif isinstance(v, list):
            new_result[k] = [mask_sensitive(str(i), mask) for i in v]
        elif isinstance(v, dict):
            new_result[k] = mask_all_sensitive_in_result(v, mask)
        else:
            new_result[k] = v
    return new_result
