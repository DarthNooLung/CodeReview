"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import DiffViewer from "react-diff-viewer-continued";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";
import ReactMarkdown from "react-markdown";
import Dropzone from "@/components/Dropzone";

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [reviewsByFile, setReviewsByFile] = useState<any[][]>([]);
  const [finalCodes, setFinalCodes] = useState<string[]>([]);
  const [originalCodes, setOriginalCodes] = useState<string[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState("gpt-3.5-turbo");
  const [summaryOnly, setSummaryOnly] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [cache, setCache] = useState<Record<string, any>>({});

  useEffect(() => {
    const darkPref = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setIsDarkMode(darkPref);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(prev => !prev);
    document.documentElement.classList.toggle("dark", !isDarkMode);
  };

  const extToLang = (ext: string) => {
    const map: Record<string, string> = {
      py: "python", java: "java", jsp: "markup", cs: "csharp", html: "html",
      js: "javascript", ts: "typescript", cpp: "cpp", c: "c"
    };
    return map[ext] || "plaintext";
  };

  const handleDrop = (droppedFiles: File[]) => {
    const allFiles = [...files, ...droppedFiles];
    setFiles(allFiles);
    setCurrentFileIndex(0);
    setCurrentChunkIndex(0);
    setReviewsByFile([]);
    setFinalCodes([]);
    const langs = allFiles.map((f) => extToLang(f.name.split(".").pop()?.toLowerCase() || "txt"));
    setLanguages(langs);

    const readers = allFiles.map(
      (file) => new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsText(file);
      })
    );

    Promise.all(readers).then(setOriginalCodes);
  };

  const removeFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
  
    setReviewsByFile([]);
    setFinalCodes([]);
    setOriginalCodes([]);
    setLanguages([]);
  
    const isDeletedFileActive = index === currentFileIndex;
    const nextIndex = Math.max(0, index - 1);
    if (isDeletedFileActive || currentFileIndex >= newFiles.length) {
      setCurrentFileIndex(nextIndex);
      setCurrentChunkIndex(0);
    }
  };

  const handleUpload = async () => {
    setLoading(true);
    const allReviews: any[][] = [];
    const finalList: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const fileKey = `${files[i].name}-${model}-${summaryOnly}`;
      if (cache[fileKey]) {
        allReviews.push(cache[fileKey].reviews);
        finalList.push(cache[fileKey].final);
        continue;
      }

      const formData = new FormData();
      formData.append("file", files[i]);
      formData.append("model", model);
      formData.append("summary_only", String(summaryOnly));

      try {
        const res = await axios.post("http://localhost:8513/review/", formData);
        allReviews.push(res.data.reviews);
        finalList.push(res.data.final_refactored);
        setCache((prev) => ({ ...prev, [fileKey]: { reviews: res.data.reviews, final: res.data.final_refactored } }));
      } catch (err) {
        allReviews.push([]);
        finalList.push("");
      }
    }

    setReviewsByFile(allReviews);
    setFinalCodes(finalList);
    setCurrentFileIndex(0);
    setCurrentChunkIndex(0);
    setLoading(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(finalCodes[currentFileIndex]);
    alert("리팩토링된 코드가 복사되었습니다.");
  };

  const handleDownload = () => {
    const blob = new Blob([finalCodes[currentFileIndex]], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `refactored.${languages[currentFileIndex]}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const currentChunks = reviewsByFile[currentFileIndex] || [];
  const currentReview = currentChunks[currentChunkIndex];

  return (
    <main className="min-h-screen p-8 bg-gray-100 dark:bg-gray-900 dark:text-white relative overflow-hidden">
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 text-black dark:text-white px-6 py-4 rounded shadow text-xl">
            파일 리뷰 중...
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold mb-4">🧠 코드 리뷰 도우미</h1>
      
      <Dropzone onFilesDrop={handleDrop} />

      <div className="flex flex-wrap gap-4 mb-4 items-center">
        <select value={model} onChange={(e) => setModel(e.target.value)} className="border p-1 rounded bg-white text-black dark:bg-gray-800 dark:text-white">
          <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          <option value="gpt-4">gpt-4</option>
          <option value="gpt-4-1106-preview">gpt-4-1106-preview</option>
        </select>
        <label className="text-sm">
          <input type="checkbox" checked={summaryOnly} onChange={(e) => setSummaryOnly(e.target.checked)} className="mr-1" />요약만 보기
        </label>
        <label className="text-sm">
          <input type="checkbox" checked={showOriginal} onChange={(e) => setShowOriginal(e.target.checked)} className="mr-1" />원본 코드 표시
        </label>
        <label className="text-sm">
          <input type="checkbox" checked={isDarkMode} onChange={toggleDarkMode} className="mr-1" />다크모드
        </label>
        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow"
          disabled={loading || files.length === 0}
        >
          파일 리뷰 요청
        </button>
      </div>

      {files.length >= 1 && (
        <div className="flex gap-2 mb-4 flex-wrap">
          {files.map((file, idx) => (
            <div key={idx} className="relative">
              <button
                onClick={() => {
                  setCurrentFileIndex(idx);
                  setCurrentChunkIndex(0);
                }}
                className={`px-3 py-1 rounded shadow text-sm ${idx === currentFileIndex ? "bg-blue-800 text-white" : "bg-white dark:bg-gray-700"}`}
              >
                {file.name}
              </button>
              <button
                onClick={() => removeFile(idx)}
                className="absolute -top-2 -right-2 text-xs bg-red-500 text-white rounded-full px-1"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {currentReview && (
        <>
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-2">📝 리뷰 요약 (Markdown)</h2>
            <div className="bg-white dark:bg-gray-800 p-4 rounded shadow prose max-w-none">
              <ReactMarkdown>{currentReview.markdown || "*리뷰 결과 없음*"}</ReactMarkdown>
            </div>
          </section>

          {!summaryOnly && (
            <>
              <section>
                <h2 className="text-xl font-semibold mb-2">🔀 코드 변경점 (Diff 보기)</h2>
                <div className="bg-white dark:bg-gray-800 p-4 rounded shadow mb-4">
                  <DiffViewer
                    oldValue={showOriginal ? originalCodes[currentFileIndex] : "(원본 코드 숨김)"}
                    newValue={currentReview.refactored_code || ""}
                    splitView={true}
                  />
                </div>

                <h2 className="text-xl font-semibold mb-2">🎯 리팩토링된 코드</h2>
                <div className="bg-white dark:bg-gray-800 p-4 rounded shadow mb-2">
                  <SyntaxHighlighter language={languages[currentFileIndex]} style={oneDark} wrapLongLines>
                    {currentReview.refactored_code || ""}
                  </SyntaxHighlighter>
                </div>

                <div className="flex gap-4">
                  <button onClick={handleCopy} className="bg-green-600 text-white px-4 py-2 rounded shadow">
                    📋 복사
                  </button>
                  <button onClick={handleDownload} className="bg-gray-700 text-white px-4 py-2 rounded shadow">
                    ⬇️ 다운로드
                  </button>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
}
