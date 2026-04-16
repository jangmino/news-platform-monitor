export type Sentiment = "긍정" | "부정" | "중립";
export type AnalysisStatus = "analyzed" | "failed" | "skipped" | "parse_error";
export type SourceFilter = "all" | "press" | "news";

export interface AnalyzedArticle {
  // 원본 press_data 필드 (보도자료)
  title: string;
  date?: string;          // 보도자료 날짜 (press)
  published_at?: string;  // 뉴스 기사 날짜 (news)
  link?: string;
  originallink?: string;  // 뉴스 원문 URL (news)
  description?: string;   // 뉴스 패시지 (news)
  content?: string;       // 보도자료 본문 (press)
  dept?: string;          // 보도자료 부처 (press)
  category?: string;
  source_type: "press" | "news";
  source_name?: string;
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

export interface NewsAnalysis {
  generated_at: string;
  total_count: number;
  analyzed_count: number;
  articles: AnalyzedArticle[];
}

export interface CombinedRecommendations {
  generated_at: string;
  source_counts: { press: number; news: number };
  policy_recommendations: PolicyRecommendation[];
}

export interface MediaOutletCount {
  domain: string;
  count: number;
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
