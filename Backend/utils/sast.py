import subprocess, tempfile, os, uuid, requests, json

SEM_GREP_RULES_PATH = "D:/003_Develop/05_Python/97.semgrep-rules/"  # 최상위 rules 폴더

# 확장자 → 해당 언어 규칙 폴더명 맵핑
RULE_LANG_MAP = {
    "java": "java",
    "js": "javascript",
    "html": "html",
    "py": "python",
    "cs": "csharp"
}

def semgrep_scan_code_detail(code: str, ext: str) -> str:
    EXT_MAP = {
        "java": "main.java",
        "js": "main.js",
        "html": "main.html",
        "py": "main.py",
        "jsp": "main.jsp",
        "cs": "main.cs",
        "aspx": "main.aspx"
    }

    # 규칙 경로 결정
    rule_subdir = RULE_LANG_MAP.get(ext, None)
    if rule_subdir:
        config_path = os.path.join(SEM_GREP_RULES_PATH, rule_subdir)
    else:
        config_path = SEM_GREP_RULES_PATH  # fallback: 전체 룰셋

    print(f"룰 경로 : {config_path}")

    filename = EXT_MAP.get(ext, f"main.{ext}")
    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        scan = subprocess.run(
            ["semgrep", f"--config={config_path}", "--json", src_path],
            capture_output=True, text=True, encoding="utf-8"
        )

        if scan.returncode != 0 and not scan.stdout:
            return "[Semgrep 실행 오류]\n" + scan.stderr

        try:
            findings = json.loads(scan.stdout)
            results = findings.get("results", [])
            parse_time = (
                findings.get("time", {})
                .get("profiling_times", {})
                .get("total_time", 0.0)
            )
            
            parseTime = f"\n⏱️ 분석 소요 시간: {parse_time:.3f}초"
            if not results:
                return f"[✅ 취약점 없음]\n이 파일에는 Semgrep 룰셋에 해당하는 보안 이슈가 발견되지 않았습니다.{parseTime}"

            formatted = []
            for r in results:
                extra = r.get("extra", {})
                meta = extra.get("metadata", {})
                #formatted.append(f"""📄 파일: {r.get('path', filename)}
                formatted.append(f"""🔢 라인: {r['start'].get('line', '?')}
⚠️ 심각도: {extra.get('severity', '정보없음')}
💬 설명: {extra.get('message', 'No message')}
📚 관련: {", ".join(meta.get('cwe', []) + meta.get('owasp', []))}
🔗 링크:
{chr(10).join(meta.get('references', [])) if meta.get('references') else '-'}{parseTime}
""")
            return "\n---\n".join(formatted)

        except Exception as e:
            return "[Semgrep 결과 파싱 오류]\n" + str(e)


def semgrep_scan_code(code: str, ext: str) -> str:
    EXT_MAP = {
        "java": "main.java",
        "js": "main.js",
        "html": "main.html",
        "py": "main.py",
        "jsp": "main.jsp",
        "cs": "main.cs",
        "aspx": "main.aspx"
    }
    # 규칙 경로 결정
    rule_subdir = RULE_LANG_MAP.get(ext, None)
    if rule_subdir:
        config_path = os.path.join(SEM_GREP_RULES_PATH, rule_subdir)
    else:
        config_path = SEM_GREP_RULES_PATH  # fallback: 전체 룰셋

    print(f"룰 경로 : {config_path}")
    
    filename = EXT_MAP.get(ext, f"main.{ext}")
    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        scan = subprocess.run(
            ["semgrep", f"--config={config_path}", "--json", src_path],
            capture_output=True, text=True, encoding="utf-8"
        )

        if scan.returncode != 0 and not scan.stdout:
            return "[Semgrep 실행 오류]\n" + scan.stderr
        
        try:
            findings = json.loads(scan.stdout)
            results = findings.get("results", [])
            if not results:
                return "[Semgrep 취약점 없음]"
            
            summary = ""
            for r in results:
                extra = r.get("extra", {})
                meta = extra.get("metadata", {})
                line = r.get("start", {}).get("line", "?")
                message = extra.get("message", "No message")
                summary += f"\n[라인: {line}] {message}\n"

            return summary.strip()

        except Exception as e:
            return "[Semgrep 결과 파싱 오류] " + str(e)

def sonarqube_scan_java_code(code: str, sonar_host: str, sonar_token: str) -> str:
    sonar_project = f"upload-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, "Main.java")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)
        # sonar-project.properties 생성
        props_path = os.path.join(tempdir, "sonar-project.properties")
        with open(props_path, "w") as f:
            f.write(f"""
sonar.projectKey={sonar_project}
sonar.sources=.
sonar.java.binaries=.
sonar.sourceEncoding=UTF-8
sonar.host.url={sonar_host}
""")
        # SonarScanner 실행
        scan = subprocess.run(
            ["sonar-scanner", f"-Dsonar.login={sonar_token}"],
            cwd=tempdir, capture_output=True, text=True
        )
        # 분석 결과를 REST API로 수집
        issues_url = f"{sonar_host}/api/issues/search?componentKeys={sonar_project}&resolved=false"
        try:
            import time
            time.sleep(3)  # SonarQube 서버가 인덱싱할 시간 약간 부여
            resp = requests.get(issues_url, auth=(sonar_token, ''))
            if resp.status_code == 200:
                issues = resp.json()
                summary = "\n".join(
                    f"- {item['message']} (Severity: {item['severity']})"
                    for item in issues.get('issues', [])[:5]
                )
                return summary or "[취약점 없음]"
            else:
                return "[SonarQube REST API 결과 조회 실패]"
        except Exception as e:
            return f"[SonarQube 이슈 조회 오류] {str(e)}"
