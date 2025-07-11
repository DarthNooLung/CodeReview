# 📄 Semgrep 도입 기술 검토 보고서

---

## 1. 도입 배경 및 목적

현대의 소프트웨어 시스템은 보안, 품질, 유지보수성을 동시에 확보해야 합니다. 특히 **운영 시스템 배포 전 코드에 존재하는 취약점, 실수, 규칙 위반 사항들을 사전에 탐지**하는 프로세스는 점점 더 중요해지고 있습니다.

현재 시스템 운영 환경에서는 다음과 같은 요구가 존재합니다:

- 배포 전 코드 안정성 확보
- 반복 가능하고 자동화된 품질 점검 루틴 필요
- 외부 감사 대응을 위한 코드 보안성 확보

따라서 본 보고서에서는 이러한 목적에 부합하는 **정적 분석 도구 Semgrep**의 도입 가능성과 적합성에 대한 기술적 검토를 진행합니다.

---

## 2. Semgrep 개요

### 2.1 Semgrep이란?

Semgrep은 수많은 글로벌 기업과 보안 전문가 커뮤니티에서 활발히 사용되고 있으며, 신뢰성과 실용성을 입증받은 도구입니다.

**🔐 주요 사용 기업:**
- **GitLab** – 코드 품질 및 보안 점검 자동화
- **Snowflake** – 내부 CI/CD 파이프라인에 정적 분석 통합
- **Dropbox** – 보안 취약점 사전 탐지 및 개발자 가이드 제공
- **Slack** – 내부 보안 기준에 맞는 룰셋 커스터마이징 활용
- **RedHat**, **Trail of Bits** 등 오픈소스 보안 분야에서 활용 중

> 이처럼 Semgrep은 신뢰도 높은 기술로, 개발자뿐 아니라 보안팀, DevSecOps 팀에게도 널리 채택되고 있습니다.


> **Semgrep(Semantic Grep)**은 코드의 **문법 구조를 분석하여 특정 패턴, 보안 취약점, 품질 문제를 탐지**하는 오픈소스 정적 분석 도구입니다.

| 항목 | 내용 |
|------|------|
| 분석 방식 | 정적 분석 (코드 실행 없이 분석) |
| 지원 언어 | Python, Java, JavaScript, C, C++, Go, HTML, JSP 등 |
| 주요 기능 | 보안 이슈 탐지, 금지 함수 사용 탐지, 스타일 체크, 사용자 정의 규칙 적용 |
| 배포 방식 | CLI 도구, Docker, GitHub Actions, CI/CD 통합 가능 |
| 라이선스 | 오픈소스 (무료 사용 가능, Enterprise 옵션 존재) |

---

### 2.2 동작 원리

Semgrep은 소스 코드를 내부적으로 추상 구문 트리(AST)로 분석하여, 사용자가 정의한 패턴과 비교함으로써 **정규식보다 정밀하고 안전한 탐지**를 수행합니다.

```yaml
# 예: 하드코딩된 패스워드 탐지 룰
rules:
  - id: hardcoded-password
    pattern: $VAR = "admin123"
    message: "하드코딩된 비밀번호가 발견되었습니다."
    severity: ERROR
```

---

## 3. 도입 필요성

### 3.1 기존 문제점

| 문제 | 설명 |
|------|------|
| 수동 코드 리뷰 한계 | 실수로 인한 누락, 피로도 증가, 일관성 부족 |
| 보안 사각지대 존재 | 배포 전 잠재적인 취약점 노출 가능성 |
| 품질 관리 체계 부족 | 내부 개발 표준 위반 여부를 사후에야 발견 |

---

### 3.2 Semgrep 도입 효과

| 기대 효과 | 설명 |
|-----------|------|
| ✅ **사전 예방적 보안 점검** | XSS, SQL Injection, 하드코딩 등 주요 보안 패턴 사전 제거 |
| ✅ **일관된 품질 기준 적용** | 팀 내 공통 규칙을 룰셋으로 적용 가능 |
| ✅ **자동화로 생산성 향상** | CI/CD 통합 시 코드 커밋 또는 PR 단계에서 자동 분석 |
| ✅ **개발자 학습 효과** | 경고 메시지를 통해 잘못된 습관을 개선 가능 |

---

## 4. 도입 적용 방안

### 4.1 적용 시나리오

1. **로컬 개발 환경에 Semgrep 설치**
2. **사내 공통 룰셋 작성**
3. **CI/CD 연동**
4. **결과 리포트 저장 및 공유**

### 4.2 적용 예시 (CI 파이프라인)

```bash
# 예: Jenkins 또는 GitHub Action에서 실행
semgrep --config ./rules/ --json --output semgrep-report.json
```

---

## 5. 기술 검토

| 항목 | 평가 내용 |
|------|-----------|
| ✔ 호환성 | 다양한 언어 지원, Python/JSP 혼합 구조에도 적합 |
| ✔ 유지보수성 | 룰셋 확장 및 버전 관리 가능 (YAML 기반 관리) |
| ✔ 커스터마이징 | 사내 보안 정책, 금지 API 등 반영한 자체 룰 제작 용이 |
| ✔ 자동화 가능성 | GitHub Actions, Jenkins, GitLab CI 등과 쉽게 통합 가능 |
| ✔ 라이선스 | 무료 오픈소스 기반, 비용 부담 없음 (상용 업그레이드 선택 가능) |
| ✔ 사용자 편의성 | CLI, VS Code 확장, 웹 UI 등 다양한 사용 방식 제공 |

> ⚠ 참고: 실제 프로젝트 환경에서는 파일 수, 코드 복잡도, 룰셋 수에 따라 분석 시간은 달라질 수 있습니다. 초기 파일럿 테스트를 통해 적정 분석 범위를 정의하는 것이 중요합니다.

---

## 6. 결론 및 제안

### ✅ 도입 제안

- **Python 기반 시스템 개발 시, Semgrep을 통한 정적 분석을 정식 절차로 도입**
- **사내 표준 RuleSet을 정의하여 코드 품질 일관성 확보**
- **CI/CD 통합을 통해 배포 전 자동 점검 체계화**

---

## 7. Semgrep vs 다른 오픈소스 정적 분석 도구 비교

정적 분석 도구는 코드 실행 없이 문제를 탐지하는 도구로, 오픈소스 생태계에서도 여러 가지가 존재합니다. Semgrep은 이 중에서도 **가독성과 커스터마이징 편의성, 멀티 언어 지원** 면에서 두각을 나타냅니다.

| 항목 | Semgrep | SonarQube (Community) | Bandit | ESLint |
|------|---------|------------------------|--------|--------|
| 지원 언어 | Python, Java, JS, C, Go 등 다수 | Java, JS 등 (플러그인 필요) | Python 전용 | JS/TS 전용 |
| 룰 정의 방식 | YAML 기반, 직관적 | Java 기반, 복잡한 설정 | 내장 룰 위주 | 플러그인 방식 |
| 사용 편의성 | CLI/웹/VS Code 지원 | 초기 설정 복잡 | 매우 단순 | 프론트엔드 친화적 |
| CI/CD 연동 | 우수 (GitHub Actions, Jenkins 등) | 가능하나 설정 필요 | 단일 스크립트 기반 | GitHub Actions 통합 쉬움 |
| 보안 취약점 탐지 | ✅ | ✅ | ✅ (Python 한정) | ❌ (코딩 스타일 중심) |
| 커스터마이징 난이도 | 낮음 (룰셋 직접 작성 가능) | 높음 (Java 개발 필요) | 낮음 | 중간 (JS 숙련도 필요) |

> Semgrep은 **다양한 언어 지원과 직관적인 룰 작성, 보안/품질 점검 통합**이라는 장점 덕분에 여러 오픈소스 도구 중에서도 범용성과 유연성 측면에서 경쟁 우위를 가집니다.


### 📌 향후 계획

1. PoC(파일럿 테스트) → 1~2개 프로젝트 적용
2. 룰셋 정제 → 사내 표준 정립
3. 전사 적용 → 신규 시스템 배포 전 필수 점검 항목 지정

---

## 부록: 설치 및 실행 요약

```bash
# 설치
pip install semgrep

# 전체 프로젝트 분석
semgrep --config auto .

# 특정 룰셋 적용
semgrep --config OWASP .

# 사용자 정의 룰 적용
semgrep --config ./my_rules/
```

---

## 📚 참고 링크

- https://semgrep.dev/
- https://github.com/returntocorp/semgrep
- https://semgrep.dev/explore
