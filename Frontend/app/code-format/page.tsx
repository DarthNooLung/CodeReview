'use client';

import { useState } from "react";
import axios from "axios";
import JSZip from "jszip";
import Dropzone from "@/components/Dropzone";

export default function CodeFormatPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<{ name: string, original: string, formatted: string, log: string }[]>([]);
  const [languages] = useState(['java', 'sql', 'jsp', 'py', 'js', 'html']);
  const [infoMessage, setInfoMessage] = useState("");
  const [engine, setEngine] = useState<"rule" | "gpt">("rule");
  const [gptModel, setGptModel] = useState("gpt-3.5-turbo");
  const [fileOptions, setFileOptions] = useState<Record<string, { indent: string; brace: string; comma: string }>>({});
  const [activeTabs, setActiveTabs] = useState<Record<string, 'original' | 'formatted'>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);

  const defaultOptions = { indent: "4", brace: "same-line", comma: "leading" };

  const handleDrop = (droppedFiles: File[]) => {
    const newFiles = droppedFiles.filter(df => !files.some(f => f.name === df.name));
    if (newFiles.length === 0) return;
    const updated = [...files, ...newFiles];
    setFiles(updated);

    const newOpts = { ...fileOptions };
    const newTabs = { ...activeTabs };
    const newExpand = { ...expanded };
    newFiles.forEach(f => {
      newOpts[f.name] = { ...defaultOptions };
      newTabs[f.name] = "formatted";
      newExpand[f.name] = true;
    });
    setFileOptions(newOpts);
    setActiveTabs(newTabs);
    setExpanded(newExpand);
    setInfoMessage(`📦 ${newFiles.length}개 파일이 추가되었습니다.`);
  };

  const updateOption = (file: string, key: string, value: string) => {
    setFileOptions(prev => ({
      ...prev,
      [file]: { ...prev[file], [key]: value }
    }));
  };

  const handleRemoveFile = (index: number) => {
    const fileName = files[index].name;
    setFiles(prev => prev.filter((_, i) => i !== index));
    setFileOptions(prev => { const copy = { ...prev }; delete copy[fileName]; return copy; });
    setActiveTabs(prev => { const copy = { ...prev }; delete copy[fileName]; return copy; });
    setExpanded(prev => { const copy = { ...prev }; delete copy[fileName]; return copy; });
    setResults(prev => prev.filter(r => r.name !== fileName));
    setInfoMessage(`❌ ${fileName} 파일이 삭제되었습니다.`);
  };

  const handleFormatAll = async () => {
    setLoading(true);
    const newResults = [];
    for (const file of files) {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (!languages.includes(ext)) continue;

      const code = await file.text();
      let formatted = "";
      let log = "";

      if (engine === "rule") {
        const opts = fileOptions[file.name];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("indent", opts.indent);
        formData.append("brace", opts.brace);
        formData.append("comma", opts.comma);
        try {
          const res = await axios.post("http://localhost:8513/format/", formData);
          formatted = res.data.formatted;
          log = `✅ 룰기반 ${opts.indent}칸, ${opts.brace}, ${opts.comma}`;
        } catch {
          formatted = "";
          log = `❌ 룰기반 처리 오류`;
        }
      } else {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("language", ext);
        formData.append("model", gptModel);
        try {
          const res = await axios.post("http://localhost:8513/gpt_format/", formData, {
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
            headers: { "Content-Type": "multipart/form-data" },
          });
          //console.log(res.data.length);
          let content = res.data || "❌ GPT 응답 없음";

          // 🔥 GPT 응답에서 ```sql ~ ``` 제거
          content = content
          .replace(/^```[a-z]*\n?/i, "")  // 시작 ```sql\n 또는 ``` 제거
          .replace(/```$/, "");           // 끝나는 ``` 제거

          formatted = content;
          log = `🤖 GPT (${gptModel}) 사용`;
        } catch {
          formatted = "";
          log = `❌ GPT 처리 오류`;
        }
      }

      newResults.push({ name: file.name, original: code, formatted, log });
    }
    setResults(newResults);
    setLoading(false);
  };

  const handleDownload = async () => {
    const zip = new JSZip();
    results.forEach(r => {
      zip.file(r.name.replace(/\.(\w+)$/, "_formatted.$1"), r.formatted);
    });
    const blob = await zip.generateAsync({ type: "blob" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "formatted_files.zip";
    link.click();
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(prev => ({ ...prev, [id]: true }));
      setTimeout(() => setCopied(prev => ({ ...prev, [id]: false })), 1500);
    });
  };

  const renderLines = (text: string) => {
    return text.split('\n').map((line, idx) =>
      <div key={idx} style={{ display: line === '' ? 'none' : 'block' }}>{line}</div>
    );
  };

  return (
    <main className="min-h-screen p-6 bg-gray-100 dark:bg-gray-900 dark:text-white">
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 text-black dark:text-white px-6 py-4 rounded shadow text-xl">
            파일 정렬 중...
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold mb-4">🧹 코드 정렬기 (룰 기반 + GPT 선택)</h1>

      <Dropzone onFilesDrop={handleDrop} />
      {infoMessage && <p className="text-blue-600 text-sm mt-2">{infoMessage}</p>}

      <div className="flex flex-wrap gap-4 items-center my-4">
        <label className="text-sm">
          정렬 방식:
          <select value={engine} onChange={e => setEngine(e.target.value as "rule" | "gpt")} className="ml-2 border p-1 rounded">
            <option value="rule">룰 기반 정렬</option>
            <option value="gpt">GPT 정렬</option>
          </select>
        </label>

        {engine === "gpt" && (
          <label className="text-sm">
            GPT 모델:
            <select value={gptModel} onChange={e => setGptModel(e.target.value)} className="ml-2 border p-1 rounded">
              <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              <option value="gpt-4">gpt-4</option>
              <option value="gpt-4o">gpt-4o</option>
            </select>
          </label>
        )}
      </div>

      {files.length > 0 && (
        <div className="space-y-2 mb-6">
          {files.map((file, idx) => {
            const opts = fileOptions[file.name];
            return (
              <div key={file.name} className="bg-white dark:bg-gray-800 rounded p-3 shadow flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <span className="font-medium">{file.name}</span>

                <div className="flex flex-col md:flex-row md:items-center md:gap-3 md:ml-auto">
                  {engine === "rule" && (
                    <div className="flex gap-2 order-1">
                      <select value={opts.indent} onChange={e => updateOption(file.name, 'indent', e.target.value)} className="border p-1 rounded">
                        <option value="2">들여쓰기 2칸</option>
                        <option value="4">들여쓰기 4칸</option>
                        <option value="tab">탭 사용</option>
                      </select>
                      <select value={opts.brace} onChange={e => updateOption(file.name, 'brace', e.target.value)} className="border p-1 rounded">
                        <option value="same-line">중괄호 same-line</option>
                        <option value="next-line">중괄호 next-line</option>
                      </select>
                      <select value={opts.comma} onChange={e => updateOption(file.name, 'comma', e.target.value)} className="border p-1 rounded">
                        <option value="leading">콤마 줄 앞</option>
                        <option value="trailing">콤마 줄 뒤</option>
                      </select>
                    </div>
                  )}
                  <button onClick={() => handleRemoveFile(idx)} className="bg-red-500 text-white px-2 py-1 rounded text-sm order-2">
                    삭제
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex gap-4 mb-6">
        <button onClick={handleFormatAll} className="bg-blue-600 text-white px-6 py-2 rounded shadow">전체 정렬 실행</button>
        <button onClick={handleDownload} className="bg-green-600 text-white px-6 py-2 rounded shadow">ZIP 저장</button>
      </div>

      {results.map((r, idx) => (
        <div key={idx} className="mb-6 border rounded bg-white dark:bg-gray-800 p-4">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-semibold">{r.name}</h2>
            <button onClick={() => setExpanded(prev => ({ ...prev, [r.name]: !prev[r.name] }))} className="text-blue-600 underline text-sm">
              {expanded[r.name] ? '접기' : '펼치기'}
            </button>
          </div>
          {expanded[r.name] && (
            <>
              <p className="text-sm text-gray-600 mb-2">{r.log}</p>
              <div className="flex gap-3 mb-2">
                <button onClick={() => setActiveTabs(prev => ({ ...prev, [r.name]: 'original' }))} className={`px-3 py-1 rounded ${activeTabs[r.name] === 'original' ? 'bg-blue-500 text-white' : 'bg-gray-300'}`}>원본 보기</button>
                <button onClick={() => setActiveTabs(prev => ({ ...prev, [r.name]: 'formatted' }))} className={`px-3 py-1 rounded ${activeTabs[r.name] === 'formatted' ? 'bg-blue-500 text-white' : 'bg-gray-300'}`}>정렬 결과</button>
                <button
                  onClick={() => {
                    const content = (activeTabs[r.name] === 'original' ? r.original : r.formatted)
                    .split('\n')
                    .filter(line => line.trim() !== '')
                    .join('\n');
                    handleCopy(content, r.name);
                  }}
                  className="px-3 py-1 rounded bg-gray-500 text-white text-sm"
                >
                  {copied[r.name] ? '✔ 복사됨' : '📋 복사'}
                </button>
              </div>
              <div className="max-h-[500px] overflow-auto whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-3 rounded text-sm">
                {renderLines(activeTabs[r.name] === 'original' ? r.original : r.formatted)}
              </div>
            </>
          )}
        </div>
      ))}
    </main>
  );
}
