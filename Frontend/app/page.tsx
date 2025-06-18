"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/code-review");
  }, [router]);

  return <p>코드 리뷰 화면으로 이동 중...</p>;
}
