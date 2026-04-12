export type Sentiment = "긍정" | "부정" | "중립";
export type AnalysisStatus = "analyzed" | "failed" | "skipped" | "parse_error";

export interface AnalyzedArticle {
  // 원본 press_data 필드
  title: string;
  date: string;
  link: string;
  content: string;
  dept: string;
  category: string;
  source_type?: string;
  file_info?: unknown;

  // Gemini 분석 결과
  platforms: string[];
  policy_domains: string[];
  risk_score: number; // 0–100
  keywords: string[]; // 최대 5개
  summary: string;
  sentiment: Sentiment;
  confidence: number; // 0–1
  status: AnalysisStatus;
  raw_response: string | null;
}

export interface PolicyRecommendation {
  title: string;
  description: string;
}

export interface PressAnalysis {
  generated_at: string;
  total_count: number;
  analyzed_count: number;
  articles: AnalyzedArticle[];
  policy_recommendations: PolicyRecommendation[];
}

// 집계 결과 타입
export interface HeatmapCell {
  platform: string;
  domain: string;
  avgRisk: number;
  count: number;
}

export interface DailyTrendPoint {
  date: string;   // "YYYY-MM-DD"
  count: number;
}

export interface KeywordFrequency {
  keyword: string;
  count: number;
  dominantDomain: string;
}

export interface BubbleCluster {
  keyword: string;
  firstDate: string;
  avgRisk: number;
  count: number;
  dominantDomain: string;
}

export interface PlatformCard {
  platform: string;
  articleCount: number;
  maxRisk: number;
  avgRisk: number;
  topKeywords: string[];
  sampleSummary: string;
}
