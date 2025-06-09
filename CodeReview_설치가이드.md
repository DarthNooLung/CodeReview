
# 💻 Code Review 프로젝트 개발환경 구성 가이드

이 문서는 Python(백엔드) 및 Next.js + Tailwind CSS(프론트엔드) 기반 프로젝트의 개발환경 구축 방법을 정리한 것입니다.
특히 Tailwind CSS 초기화 과정에서 발생했던 이슈와 그 해결법을 상세히 다룹니다.

---

## 🧱 환경 구성 개요

- 운영체제: Windows
- 쉘: Git Bash
- Node.js: v22.16.0
- Python: 3.11.9
- 프론트엔드: Next.js (v15.3.3)
- 백엔드: FastAPI
- CSS 프레임워크: Tailwind CSS

---

## 📦 Python 백엔드 환경 구성

### 1. 가상환경 생성 및 실행
```bash
python -m venv venv
source venv/Scripts/activate  # Git Bash 전용
```

### 2. 의존성 설치
```bash
pip install fastapi uvicorn[standard] python-dotenv openai
```

### 3. 실행
```bash
uvicorn main:app --reload --port 8513

python -m uvicorn main:app --reload --port 8513
```

---

## 💻 Node.js + Tailwind 프론트엔드 환경 구성

### 1. 프로젝트 초기화
```bash
cd Frontend
npm init -y
```

### 2. 의존성 설치 (성공한 최종 버전 명시)
```bash
npm install -D tailwindcss@3.4.3 postcss autoprefixer
npm install react-diff-viewer-continued react-syntax-highlighter --legacy-peer-deps
```

### ✅ Tailwind 설치 실패 해결법 요약
- `tailwindcss-cli`를 설치하지 마세요 (`npx`가 실행 파일을 인식 못함)
- `tailwindcss@latest`가 정상적으로 `.bin/tailwindcss`를 생성하지 않으면 `@3.4.3` 버전 명시
- 설치 후 반드시 실행 파일 존재 확인:
  ```bash
  ls node_modules/.bin | grep tailwindcss
  ```

### 3. Tailwind 초기화
```bash
npx tailwindcss init -p
```

### 4. Tailwind 설정 (`tailwind.config.js`)
```js
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 5. 글로벌 CSS 설정 (`app/globals.css`)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 6. globals.css import (`layout.tsx` 또는 `_app.tsx`)
```tsx
import './globals.css'
```

### 7. 실행
```bash
npx next dev -p 8514
```


---

## 🌐 .env 파일 및 API 연결 설정

### 1. 백엔드 `.env` 파일 예시
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. 프론트엔드에서 백엔드 API URL 설정 예시

#### `.env.local` 파일 생성 (Frontend 디렉토리 내)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8513
```

#### 사용 예시 (프론트 코드 내 fetch)
```ts
const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/analyze`, {
  method: "POST",
  body: formData,
});
```

> `NEXT_PUBLIC_` 접두사는 **Next.js에서 브라우저 환경에서도 접근 가능한 환경 변수**로 필수입니다.
---

## 🧩 기타 팁

- `.env` 파일에 OpenAI API 키 지정 필요:
```bash
OPENAI_API_KEY=sk-xxxxxx
```

- 필요 시 `.env.example`, `README.md`, `requirements.txt` 등을 추가해두면 좋습니다.

---

이 문서를 통해 문제 없이 개발환경이 재현되도록 구성되었습니다.
