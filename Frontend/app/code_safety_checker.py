#!/usr/bin/env python3
import re
from pathlib import Path

# 검사 대상 파일
source_file = Path("page.tsx")

# 읽기
code = source_file.read_text(encoding="utf-8")

# 의심스러운 패턴 탐색: 예) setLoadin( 처럼 끝나는 변수, 함수명
suspicious = re.findall(r'\b\w{5,}[^\w\d]\(', code)
partial_names = [s for s in suspicious if not re.search(r'\bsetLoading\(', s)]

# 줄 단위로 위치 확인
results = []
lines = code.splitlines()
for i, line in enumerate(lines):
    if re.search(r'\b\w{5,}\(', line) and not re.search(r'\bsetLoading\(', line):
        if re.search(r'setLoadin\(', line):
            results.append(f"[Line {i+1}] {line.strip()}")

# 출력
if results:
    print("⚠️ Suspected truncated/partial identifier usage:")
    for r in results:
        print(r)
else:
    print("✅ No suspicious identifier truncation found.")
