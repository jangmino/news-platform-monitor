import { useState, useEffect } from "react";
import type { PressAnalysis } from "@/types/analysis";

interface UseAnalysisDataResult {
  data: PressAnalysis | null;
  isLoading: boolean;
  error: string | null;
}

const EMPTY: PressAnalysis = {
  generated_at: "",
  total_count: 0,
  analyzed_count: 0,
  articles: [],
  policy_recommendations: [],
};

export function useAnalysisData(): UseAnalysisDataResult {
  const [data, setData] = useState<PressAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch("/data/press_analysis.json")
      .then((res) => {
        if (!res.ok) {
          if (res.status === 404) {
            // 파일 없음 → 빈 상태 표시
            return EMPTY;
          }
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json() as Promise<PressAnalysis>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setIsLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          // 로컬 환경에서 파일이 없을 때 fetch 자체가 실패하는 경우
          if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
            setData(EMPTY);
          } else {
            setError(msg);
          }
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, isLoading, error };
}
