#!/bin/bash

echo "🚀 [1/6] Python + Next.js 개발 환경 초기화 시작..."

# --- .gitignore 생성 ---
cat <<'EOF' > .gitignore
# Node.js / Next.js
node_modules/
.next/
out/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
package-lock.json
.env*
*.local

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.pyc
*.so
*.egg-info/
.eggs/
build/
dist/
*.log
*.sqlite3
*.db
*.coverage
.venv/
venv/
ENV*/
env*/
pip-wheel-metadata/
*.manifest

# Jupyter
.ipynb_checkpoints

# IDE / OS
.DS_Store
.vscode/
.idea/
EOF

echo "✅ .gitignore 생성 완료"

# --- .gitattributes 생성 ---
cat <<'EOF' > .gitattributes
* text=auto
*.py linguist-language=Python
*.js linguist-language=JavaScript
*.ts linguist-language=TypeScript
*.png binary
*.jpg binary
*.jpeg binary
*.mp4 binary
*.ttf binary
EOF

echo "✅ .gitattributes 생성 완료"

# --- pre-commit 설치 ---
echo "📦 [2/6] Python pre-commit 설치"
pip install pre-commit > /dev/null 2>&1

cat <<'EOF' > .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/prettier/prettier
    rev: v3.2.4
    hooks:
      - id: prettier
        files: '\.(js|ts|tsx|jsx|json|css|scss|md)$'

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-merge-conflict
      - id: end-of-file-fixer
      - id: trailing-whitespace
EOF

pre-commit install
echo "✅ pre-commit 구성 완료"

# --- Next.js 관련 패키지 설치 ---
echo "📦 [3/6] Next.js Prettier + ESLint 설치 중..."
npm install -D prettier eslint > /dev/null 2>&1

# --- package.json 설정 보완 ---
echo "📄 [4/6] package.json 스크립트 추가"
if [ -f "package.json" ]; then
  node -e '
    const fs = require("fs");
    const pkg = JSON.parse(fs.readFileSync("package.json"));
    pkg.scripts = Object.assign(pkg.scripts || {}, {
      "lint": "next lint",
      "format": "prettier --write ."
    });
    pkg.prettier = {
      "semi": true,
      "singleQuote": true,
      "tabWidth": 2,
      "trailingComma": "es5"
    };
    pkg.eslintConfig = {
      "extends": ["next/core-web-vitals"]
    };
    fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2));
  '
else
  echo "⚠️ package.json 파일이 없습니다. 수동으로 추가해주세요."
fi

# --- 완료 메시지 ---
echo "🎉 [6/6] 개발 환경 세팅 완료!"
echo "🔧 pre-commit 자동 적용 완료 (commit 시 자동 포맷)"
echo "📁 생성 파일: .gitignore, .gitattributes, .pre-commit-config.yaml"