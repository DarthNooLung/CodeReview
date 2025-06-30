"use client";

import { useState } from "react";
import axios from "axios";
import Dropzone from "@/components/Dropzone";

export default function SastOnlyPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [sastResults, setSastResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState<number | null>(null);
  const [useGptFeedback, setUseGptFeedback] = useState(false);
  const [gptModel, setGptModel] = useState("gpt-3.5-turbo");

  const handleDrop = (droppedFiles: File[]) => {
    setFiles([...files, ...droppedFiles]);
    setCurrentFileIndex(0);
    setSastResults([]);
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);

    const newResults = [...sastResults];
    newResults.splice(index, 1);
    setSastResults(newResults);

    if (index === currentFileIndex) {
      setCurrentFileIndex(0);
    } else if (index < currentFileIndex) {
      setCurrentFileIndex(prev => Math.max(0, prev - 1));
    }
  };

  const handleUpload = async () => {
    setLoading(true);
    setCurrentProcessingIndex(0);
    const allSastResults: string[] = [];

    for (let i = 0; i < files.length; i++) {
      setCurrentProcessingIndex(i + 1); // 1-based index
      const formData = new FormData();
      formData.append("file", files[i]);
      formData.append("use_gpt_feedback", String(useGptFeedback));
      formData.append("gpt_model", gptModel);

      try {
        const res = await axios.post("http://localhost:8513/sast/", formData);
        allSastResults.push(res.data.sast_result || "");
      } catch {
        allSastResults.push("[정적분석 실패]");
      }
    }

    setSastResults(allSastResults);
    setLoading(false);
    setCurrentProcessingIndex(null);
  };

  const handleCopySast = () => {
    navigator.clipboard.writeText(sastResults[currentFileIndex] || "");
    alert("정적분석 결과가 복사되었습니다.");
  };

  const handleDownloadSast = () => {
    const blob = new Blob([sastResults[currentFileIndex] || ""], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${files[currentFileIndex]?.name || "sast_result"}.sast.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <main className="min-h-screen p-8 bg-gray-100 dark:bg-gray-900 dark:text-white">
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 text-black dark:text-white px-6 py-4 rounded shadow text-xl">
            {currentProcessingIndex
              ? `정적분석 중... (${currentProcessingIndex} / ${files.length})`
              : "정적분석 준비 중..."}
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold mb-4">🛡️ 정적분석 도우미</h1>
      <Dropzone onFilesDrop={handleDrop} />

      <div className="flex items-center gap-4 my-4">
        <select value={gptModel} onChange={(e) => setGptModel(e.target.value)} className="border rounded px-2 py-1 dark:bg-gray-700 dark:text-white">
          <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          <option value="gpt-4">gpt-4</option>
          <option value="gpt-4-1106-preview">gpt-4-1106-preview</option>
        </select>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={useGptFeedback} onChange={(e) => setUseGptFeedback(e.target.checked)} />
          <span>문제 발생 시 GPT 개선 피드백 받기</span>
        </label>
      </div>

      {/* 버튼 + 파일 목록 */}
      <div className="flex items-center gap-4 my-6 flex-wrap">
        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow"
          disabled={loading || files.length === 0}
        >
          정적분석 요청
        </button>

        {files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map((file, idx) => (
              <div key={idx} className="relative">
                <button
                  onClick={() => setCurrentFileIndex(idx)}
                  className={`px-3 py-1 rounded shadow text-sm ${
                    idx === currentFileIndex
                      ? "bg-blue-800 text-white"
                      : "bg-white dark:bg-gray-700"
                  }`}
                >
                  {file.name}
                </button>
                <button
                  onClick={() => handleRemoveFile(idx)}
                  className="absolute -top-2 -right-2 text-xs bg-red-500 text-white rounded-full px-1"
                  title="파일 삭제"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 정적분석 결과 표시 */}
      {sastResults[currentFileIndex] && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-2">🔍 정적분석 결과</h2>
          <div className="bg-white dark:bg-gray-800 p-4 rounded shadow whitespace-pre-wrap break-words">
            {sastResults[currentFileIndex]}
          </div>
          <div className="flex gap-4 mt-2">
            <button
              onClick={handleCopySast}
              className="bg-green-600 text-white px-4 py-2 rounded shadow"
            >
              📋 결과 복사
            </button>
            <button
              onClick={handleDownloadSast}
              className="bg-gray-700 text-white px-4 py-2 rounded shadow"
            >
              ⬇️ 결과 다운로드
            </button>
          </div>
        </section>
      )}
    </main>
  );
}
