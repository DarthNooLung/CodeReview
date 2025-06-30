"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import DiffViewer from "react-diff-viewer-continued";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";
import ReactMarkdown from "react-markdown";
import Dropzone from "@/components/Dropzone";

function extractReviewSections(markdown: string) {
  // 숫자 + 마침표 접두어 제거 (줄 시작만)
  const cleaned = markdown.replace(/(^|\n)\d+\.\s*(?=(기능 설명|개선이 필요한 부분|주요 변경 요약|리팩토링 코드))/g, '$1');

  // 주요 변경 요약을 개선에 포함시키기 위해 통합 처리
  const review = cleaned.match(/기능 설명[:：]?\s*\n?([\s\S]*?)(?=\n+(개선이 필요한 부분[:：]|리팩토링 코드[:：]|$))/);
  const improvementBlock = cleaned.match(/개선이 필요한 부분[:：]?\s*\n?([\s\S]*?)(?=\n+주요 변경 요약[:：]|$)/);
  const changesBlock = cleaned.match(/주요 변경 요약[:：]?\s*\n?([\s\S]*?)(?=\n+리팩토링 코드[:：]|$)/);
  const refactor = cleaned.match(/리팩토링 코드[:：]?\s*\n?([\s\S]*)/);

  return {
    review: review?.[1]?.trim() || "",
    improvement: improvementBlock?.[1]?.trim() || "",
    changes: changesBlock?.[1]?.trim() || "",
    refactor: refactor?.[1]?.trim() || ""
  };
}


export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [reviewsByFile, setReviewsByFile] = useState<any[][]>([]);
  const [finalCodes, setFinalCodes] = useState<string[]>([]);
  const [originalCodes, setOriginalCodes] = useState<string[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [sastResults, setSastResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState("gpt-3.5-turbo");
  const [showSummary, setShowSummary] = useState(true);
  const [showDiff, setShowDiff] = useState(true);
  const [showOriginal, setShowOriginal] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showSast, setShowSast] = useState(true);
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
      js: "javascript", ts: "typescript", cpp: "cpp", c: "c", aspx: "markup"
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
    setSastResults([]);
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
    setSastResults([]);
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
    const allSastResults: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const fileKey = `${files[i].name}-${model}`;
      if (cache[fileKey]) {
        allReviews.push(cache[fileKey].reviews);
        finalList.push(cache[fileKey].final);
        allSastResults.push(cache[fileKey].sast || "");
        continue;
      }

      const formData = new FormData();
      formData.append("file", files[i]);
      formData.append("model", model);

      try {
        const res = await axios.post("http://localhost:8513/review/", formData);
        allReviews.push(res.data.reviews);
        finalList.push(res.data.final_refactored);
        allSastResults.push(res.data.sast_result || "");
        setCache((prev) => ({
          ...prev,
          [fileKey]: {
            reviews: res.data.reviews,
            final: res.data.final_refactored,
            sast: res.data.sast_result || ""
          }
        }));
      } catch (err) {
        allReviews.push([]);
        finalList.push("");
        allSastResults.push("[정적분석 결과 없음]");
      }
    }

    setReviewsByFile(allReviews);
    setFinalCodes(finalList);
    setSastResults(allSastResults);
    setCurrentFileIndex(0);
    setCurrentChunkIndex(0);
    setLoading(false);
  };

  // 정적분석 결과 복사
  const handleCopySast = () => {
    navigator.clipboard.writeText(sastResults[currentFileIndex] || "");
    alert("정적분석 결과가 복사되었습니다.");
  };

  // 정적분석 결과 다운로드
  const handleDownloadSast = () => {
    const blob = new Blob([sastResults[currentFileIndex] || ""], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${files[currentFileIndex]?.name || "sast_result"}.sast.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <input type="checkbox" checked={showSast} onChange={e => setShowSast(e.target.checked)} className="mr-1" />정적분석 보기
        </label>
        <label className="text-sm">
          <input type="checkbox" checked={showSummary} onChange={(e) => setShowSummary(e.target.checked)} className="mr-1" />요약 보기
        </label>
        <label className="text-sm">
          <input type="checkbox" checked={showDiff} onChange={(e) => setShowDiff(e.target.checked)} className="mr-1" />코드 변경점 보기
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

      {/* 기존 리뷰/코드 영역 (정적분석, 결합 요약 포함) */}
      {currentReview && (
        <>
          {showSast && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold mb-2">🛡️ 정적분석 결과</h2>
              <div className="bg-white dark:bg-gray-800 p-4 rounded shadow whitespace-pre-wrap max-w-none break-all">
                {sastResults[currentFileIndex]}
              </div>
              <div className="flex gap-4 mt-2">
                <button
                  onClick={handleCopySast}
                  className="bg-green-600 text-white px-4 py-2 rounded shadow"
                >
                  📋 정적분석 결과 복사
                </button>
                <button
                  onClick={handleDownloadSast}
                  className="bg-gray-700 text-white px-4 py-2 rounded shadow"
                >
                  ⬇️ 정적분석 결과 다운로드
                </button>
              </div>
            </section>
          )}

          {showSummary && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold mb-2">📝 리뷰 요약</h2>
              <div className="bg-white dark:bg-gray-800 p-4 rounded shadow prose max-w-none whitespace-pre-wrap">
                {(() => {
                  const { review, improvement, changes, refactor } = extractReviewSections(currentReview.markdown || "");
          
                  return (
                    <>
                      <h3 className="text-lg font-semibold mt-4 mb-1">🧠 기능 설명</h3>
                      <p>&nbsp;&nbsp;&nbsp;&nbsp;{review || "없음"}</p>
          
                      <h3 className="text-lg font-semibold mt-4 mb-1">🔧 개선이 필요한 부분</h3>
                      <p>&nbsp;&nbsp;&nbsp;&nbsp;{improvement || "없음"}</p>

                      <h3 className="text-lg font-semibold mt-4 mb-1">📌 주요 변경 요약</h3>
                      <p>&nbsp;&nbsp;&nbsp;&nbsp;{changes || "없음"}</p>
          
                      <h3 className="text-lg font-semibold mt-4 mb-1">🛠️ 리팩토링 코드</h3>
                      <SyntaxHighlighter language={languages[currentFileIndex]} style={oneDark} wrapLongLines>
                        {refactor || "// 없음"}
                      </SyntaxHighlighter>
                    </>
                  );
                })()}
              </div>
            </section>
          )}

          {showDiff && (
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
