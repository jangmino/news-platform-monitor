import { useState, useEffect } from "react";
import type {
  AnalyzedArticle,
  PolicyRecommendation,
  PressAnalysis,
  NewsAnalysis,
  CombinedRecommendations,
} from "@/types/analysis";

export interface CombinedDataResult {
  pressArticles: AnalyzedArticle[];
  newsArticles: AnalyzedArticle[];
  combinedRecs: PolicyRecommendation[];
  pressRecs: PolicyRecommendation[];
  pressGeneratedAt: string;
  newsGeneratedAt: string;
  isLoading: boolean;
  error: string | null;
}

async function fetchJSON<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json() as T;
    return json;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) return null;
    throw err;
  }
}

export function useAnalysisData(): CombinedDataResult {
  const [state, setState] = useState<CombinedDataResult>({
    pressArticles: [],
    newsArticles: [],
    combinedRecs: [],
    pressRecs: [],
    pressGeneratedAt: "",
    newsGeneratedAt: "",
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      fetchJSON<PressAnalysis>("/data/press_analysis.json"),
      fetchJSON<NewsAnalysis>("/data/news_analysis.json"),
      fetchJSON<CombinedRecommendations>("/data/combined_recommendations.json"),
    ]).then(([pressResult, newsResult, recsResult]) => {
      if (cancelled) return;

      let error: string | null = null;

      // 보도자료 분석 결과
      let pressArticles: AnalyzedArticle[] = [];
      let pressRecs: PolicyRecommendation[] = [];
      let pressGeneratedAt = "";
      if (pressResult.status === "fulfilled" && pressResult.value) {
        pressArticles = (pressResult.value.articles ?? []).map((a) => ({
          ...a,
          source_type: "press" as const,
        }));
        pressRecs = pressResult.value.policy_recommendations ?? [];
        pressGeneratedAt = pressResult.value.generated_at ?? "";
      } else if (pressResult.status === "rejected") {
        error = pressResult.reason instanceof Error
          ? pressResult.reason.message
          : String(pressResult.reason);
      }

      // 뉴스 분석 결과
      let newsArticles: AnalyzedArticle[] = [];
      let newsGeneratedAt = "";
      if (newsResult.status === "fulfilled" && newsResult.value) {
        newsArticles = (newsResult.value.articles ?? []).map((a) => ({
          ...a,
          source_type: "news" as const,
        }));
        newsGeneratedAt = newsResult.value.generated_at ?? "";
      } else if (newsResult.status === "rejected" && !error) {
        error = newsResult.reason instanceof Error
          ? newsResult.reason.message
          : String(newsResult.reason);
      }

      // 통합 정책 제언
      let combinedRecs: PolicyRecommendation[] = [];
      if (recsResult.status === "fulfilled" && recsResult.value) {
        combinedRecs = recsResult.value.policy_recommendations ?? [];
      }

      setState({
        pressArticles,
        newsArticles,
        combinedRecs,
        pressRecs,
        pressGeneratedAt,
        newsGeneratedAt,
        isLoading: false,
        error,
      });
    });

    return () => { cancelled = true; };
  }, []);

  return state;
}
