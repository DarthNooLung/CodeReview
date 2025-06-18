"use client";

import React, { useCallback, useState } from "react";

interface DropzoneProps {
  onFilesDrop: (files: File[]) => void;
}

export default function Dropzone({ onFilesDrop }: DropzoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    onFilesDrop(files);
  }, [onFilesDrop]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  }, []);

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`w-full p-8 mb-4 rounded-lg text-center transition-all duration-200 cursor-pointer
        border-4 ${dragging ? "border-blue-500 bg-blue-100 dark:bg-blue-900" : "border-gray-300 bg-gray-200 dark:bg-gray-700"}
        text-gray-700 dark:text-gray-200`}
    >
      <p className="text-lg font-semibold">📥 파일을 이곳에 드래그 앤 드롭</p>
      <p className="text-sm text-gray-500 dark:text-gray-300" style={{ display: 'none' }}>(또는 아래에서 수동으로 선택하세요)</p>
    </div>
  );
}
