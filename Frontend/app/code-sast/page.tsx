"use client";

import { useState } from "react";
import axios from "axios";
import Dropzone from "@/components/Dropzone";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export default function SastOnlyPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [sastResults, setSastResults] = useState<(any[] | string)[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState<number | null>(null);
  const [useGptFeedback, setUseGptFeedback] = useState(false);
  const [gptModel, setGptModel] = useState("gpt-3.5-turbo");
  const [totalElapsed, setTotalElapsed] = useState<number | null>(null);

  /** ----------- File Upload Handling ----------- **/
  const handleDrop = (droppedFiles: File[]) => {
    setFiles([...files, ...droppedFiles]);
    setCurrentFileIndex(0);
    setSastResults([]);
    setTotalElapsed(null);
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

  /** ----------- Upload to Server ----------- **/
  const handleUpload = async () => {
    setLoading(true);
    setCurrentProcessingIndex(0);
    setTotalElapsed(null);

    const startTime = Date.now();

    const allResults: (any[] | string)[] = [];

    for (let i = 0; i < files.length; i++) {
      setCurrentProcessingIndex(i + 1);

      const formData = new FormData();
      formData.append("file", files[i]);
      formData.append("use_gpt_feedback", String(useGptFeedback));
      formData.append("gpt_model", gptModel);

      try {
        const res = await axios.post("http://localhost:8513/sast/", formData);
        if (res.data?.error) {
          allResults.push(`[❌ 서버 오류]\n${res.data.error}\n${res.data.details || ''}`);
        } else {
          allResults.push(res.data.sast_result || []);
        }
      } catch (err: any) {
        allResults.push(`[❌ 요청 실패]\n${err?.message || 'Unknown error'}`);
      }
    }

    const endTime = Date.now();
    setTotalElapsed((endTime - startTime) / 1000);

    setSastResults(allResults);
    setLoading(false);
    setCurrentProcessingIndex(null);
  };

  /** ----------- Copy / Save / PDF Helpers ----------- **/
  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    alert("📋 복사되었습니다.");
  };

  const saveText = (text: string, filename: string = "sast_result.txt") => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const savePdf = async () => {
    const target = document.getElementById("pdf-content");
    if (!target) return;
  
    const toHide = target.querySelectorAll(".pdf-exclude");
    toHide.forEach(el => el.classList.add("hidden"));
  
    const pdf = new jsPDF("p", "mm", "a4");
  
    // ✅ scale 낮춰서 캡처 해상도 줄이기
    const canvas = await html2canvas(target, { scale: 1.2 });
  
    const imgData = canvas.toDataURL("image/jpeg", 0.7); 
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
  
    // ✅ JPEG 포맷 + 퀄리티 조정
    pdf.addImage(imgData, "JPEG", 0, 0, pdfWidth, pdfHeight, undefined, 'FAST');
    //pdf.save(`${files[currentFileIndex]?.name || "sast_result"}.pdf`);
    // 파일명 규칙: 정적분석_파일명.png
    const baseFileName = files[currentFileIndex]?.name?.split(".")[0] || "결과";
    const finalFileName = `정적분석_${baseFileName}.pdf`;
    pdf.save(finalFileName)
  
    toHide.forEach(el => el.classList.remove("hidden"));
  };

  const saveImage = async () => {
    const target = document.getElementById("pdf-content");
    if (!target) return;
  
    // PDF에서 하던 것과 똑같이 버튼 숨기기
    const toHide = target.querySelectorAll(".pdf-exclude");
    toHide.forEach(el => el.classList.add("hidden"));
  
    // 캡처
    const canvas = await html2canvas(target, { scale: 1.3 });
  
    // 이미지 데이터
    const imgData = canvas.toDataURL("image/png");
  
    // 다운로드 링크 생성
    const link = document.createElement("a");
    link.href = imgData;
    //link.download = `${files[currentFileIndex]?.name || "sast_result"}.png`;
    // 파일명 규칙: 정적분석_파일명.png
    const baseFileName = files[currentFileIndex]?.name?.split(".")[0] || "결과";
    const finalFileName = `정적분석_${baseFileName}.png`;
    link.download = finalFileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  
    // 버튼 복원
    toHide.forEach(el => el.classList.remove("hidden"));
  };

  const handleCopyAll = () => {
    const current = sastResults[currentFileIndex];
    if (!current) return;

    let text = "";
    if (typeof current === "string") {
      text = current;
    } else {
      text = current
        .map((langRes: any) =>
          [`📌 ${langRes.language} (⏱️ ${langRes.parse_time?.toFixed(3)}초)`, ...(langRes.results || [])].join("\n\n")
        )
        .join("\n\n---\n\n");
    }
    copyText(text);
  };

  const handleDownloadAll = () => {
    const current = sastResults[currentFileIndex];
    if (!current) return;

    let text = "";
    if (typeof current === "string") {
      text = current;
    } else {
      text = current
        .map((langRes: any) =>
          [`📌 ${langRes.language} (⏱️ ${langRes.parse_time?.toFixed(3)}초)`, ...(langRes.results || [])].join("\n\n")
        )
        .join("\n\n---\n\n");
    }
    saveText(text, `${files[currentFileIndex]?.name || "sast_result"}.sast.txt`);
  };

  /** ----------- Rendering ----------- **/
  const currentResult = sastResults[currentFileIndex];

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
        <select
          value={gptModel}
          onChange={(e) => setGptModel(e.target.value)}
          className="border rounded px-2 py-1 dark:bg-gray-700 dark:text-white"
        >
          <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          <option value="gpt-4">gpt-4</option>
          <option value="gpt-4-1106-preview">gpt-4-1106-preview</option>
        </select>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={useGptFeedback}
            onChange={(e) => setUseGptFeedback(e.target.checked)}
          />
          <span>문제 발생 시 GPT 개선 피드백 받기</span>
        </label>
      </div>

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

      <section id="pdf-content" className="mb-8">
        {totalElapsed && (
          <div className="my-4 p-4 rounded shadow bg-yellow-50 dark:bg-yellow-900 text-black dark:text-white pdf-exclude">
            🚀 총 처리시간 (요청~응답): {totalElapsed.toFixed(2)}초
          </div>
        )}

        {typeof currentResult === 'string' && (
          <>
            <h2 className="text-xl font-semibold mb-2">❌ 분석 실패 / 오류 메시지</h2>
            <div className="bg-red-100 dark:bg-red-900 p-4 rounded shadow whitespace-pre-wrap break-words">
              {currentResult
                .split('\n')
                .filter(Boolean)
                .map((line, idx) => (
                  <div key={idx} className="flex justify-between items-center border-b py-1">
                    <span className="break-words">{line}</span>
                    <button
                      onClick={() => copyText(line)}
                      className="text-xs bg-green-600 text-white px-2 py-1 rounded pdf-exclude"
                    >
                      📋
                    </button>
                  </div>
                ))}
            </div>
            <div className="flex gap-4 mt-2">
              <button
                onClick={handleCopyAll}
                className="bg-green-600 text-white px-4 py-2 rounded shadow pdf-exclude"
              >
                📋 전체 복사
              </button>
              <button
                onClick={handleDownloadAll}
                className="bg-gray-700 text-white px-4 py-2 rounded shadow pdf-exclude"
              >
                ⬇️ 내용 저장
              </button>
              <button
                onClick={saveImage}
                className="bg-purple-700 text-white px-4 py-2 rounded shadow"
              >
                ⬇️ 이미지 저장
              </button>
            </div>
          </>
        )}

        {Array.isArray(currentResult) && (
          <>
            <h2 className="text-xl font-semibold mb-2">🔍 정적분석 결과</h2>
            {currentResult.length === 0 && (
              <div className="bg-white dark:bg-gray-800 p-4 rounded shadow">
                [✅ 분석결과 없음]
              </div>
            )}
            {currentResult.map((langResult: any, idx: number) => (
              <div
                key={idx}
                className="bg-white dark:bg-gray-800 p-4 rounded shadow mb-4 whitespace-pre-wrap break-words"
              >
                <h3 className="text-lg font-bold mb-2">
                  📌 {langResult.language}
                  {langResult.parse_time && ` (⏱️ 정적 분석 시간: ${langResult.parse_time.toFixed(3)}초)`}
                </h3>
                {langResult.results?.map((line: string, i: number) => (
                  <div key={i} className="flex justify-between items-center border-b py-3">
                    <span className="break-words">{line}</span>
                    <button
                      onClick={() => copyText(line)}
                      className="text-xs bg-green-600 text-white px-2 py-1 rounded pdf-exclude"
                    >
                      📋
                    </button>
                  </div>
                ))}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => copyText(langResult.results.join('\n'))}
                    className="bg-green-600 text-white px-3 py-1 rounded shadow text-sm pdf-exclude"
                  >
                    📋 내용 복사
                  </button>
                  <button
                    onClick={() => saveText(langResult.results.join('\n'))}
                    className="bg-gray-700 text-white px-3 py-1 rounded shadow text-sm pdf-exclude"
                  >
                    ⬇️ 내용 저장
                  </button>
                  <button
                    onClick={saveImage}
                    className="bg-purple-700 text-white px-3 py-1 rounded shadow text-sm pdf-exclude"
                  >
                    ⬇️ 이미지 저장
                  </button>
                </div>
              </div>
            ))}
          </>
        )}
      </section>
    </main>
  );
}
