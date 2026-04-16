import type {
  AnalyzedArticle,
  BubbleCluster,
  DailyTrendPoint,
  HeatmapCell,
  KeywordFrequency,
  MediaOutletCount,
  PlatformCard,
} from "@/types/analysis";

/** 분석 완료 기사만 필터링 */
function analyzed(articles: AnalyzedArticle[]): AnalyzedArticle[] {
  return articles.filter((a) => a.status === "analyzed");
}

/** 기사의 날짜 문자열 반환 — press: date, news: published_at 순으로 확인 */
function articleDate(a: AnalyzedArticle): string {
  return a.date ?? a.published_at ?? "";
}

/** ISO "YYYY-MM-DD" 변환 (RFC 2822 등 다양한 형식 대응) */
function toISODate(dateStr: string): string {
  if (!dateStr) return "unknown";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "unknown";
  return d.toISOString().slice(0, 10);
}

// ─── 날짜 범위 필터 ──────────────────────────────────────────────────────────

/** days가 null이면 전체, 숫자면 최근 N일 기사만 반환 */
export function filterByDateRange(
  articles: AnalyzedArticle[],
  days: number | null
): AnalyzedArticle[] {
  if (!days) return articles;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  return articles.filter((a) => {
    const ds = articleDate(a);
    if (!ds) return false;
    const d = new Date(ds);
    return !isNaN(d.getTime()) && d >= cutoff;
  });
}

// ─── 섹션 1: 히트맵 ────────────────────────────────────────────────────────

/**
 * 플랫폼 × 정책영역 매트릭스 → 평균 risk_score
 */
export function buildHeatmapMatrix(
  articles: AnalyzedArticle[],
  platforms: string[],
  domains: string[]
): HeatmapCell[] {
  const map = new Map<string, Map<string, { sum: number; count: number }>>();

  for (const a of analyzed(articles)) {
    const ps = a.platforms.length > 0 ? a.platforms : ["기타"];
    const ds = a.policy_domains.length > 0 ? a.policy_domains : ["기타"];

    for (const p of ps) {
      for (const d of ds) {
        if (!map.has(p)) map.set(p, new Map());
        const inner = map.get(p)!;
        const prev = inner.get(d) ?? { sum: 0, count: 0 };
        inner.set(d, { sum: prev.sum + a.risk_score, count: prev.count + 1 });
      }
    }
  }

  const allPlatforms = [...platforms, "기타"];
  const allDomains = [...domains, "기타"];
  const cells: HeatmapCell[] = [];

  for (const p of allPlatforms) {
    for (const d of allDomains) {
      const entry = map.get(p)?.get(d);
      cells.push({
        platform: p,
        domain: d,
        avgRisk: entry ? Math.round(entry.sum / entry.count) : 0,
        count: entry?.count ?? 0,
      });
    }
  }

  return cells;
}

// ─── 섹션 1: 정책영역 통계 ──────────────────────────────────────────────────

export interface DomainStat {
  domain: string;
  count: number;
  avgRisk: number;
}

/** 정책영역별 기사 수 + 평균 리스크 */
export function buildDomainStats(articles: AnalyzedArticle[]): DomainStat[] {
  const map = new Map<string, { risks: number[] }>();

  for (const a of analyzed(articles)) {
    const ds = a.policy_domains.length > 0 ? a.policy_domains : ["기타"];
    for (const d of ds) {
      if (!map.has(d)) map.set(d, { risks: [] });
      map.get(d)!.risks.push(a.risk_score);
    }
  }

  return Array.from(map.entries())
    .map(([domain, { risks }]) => ({
      domain,
      count: risks.length,
      avgRisk: risks.length
        ? Math.round(risks.reduce((s, r) => s + r, 0) / risks.length)
        : 0,
    }))
    .sort((a, b) => b.count - a.count);
}

// ─── 섹션 1: 감성 통계 ──────────────────────────────────────────────────────

export interface SentimentStat {
  sentiment: string;
  count: number;
}

/** 감성(긍정/부정/중립) 분포 */
export function buildSentimentStats(articles: AnalyzedArticle[]): SentimentStat[] {
  const map = new Map<string, number>();
  for (const a of analyzed(articles)) {
    map.set(a.sentiment, (map.get(a.sentiment) ?? 0) + 1);
  }
  return Array.from(map.entries()).map(([sentiment, count]) => ({ sentiment, count }));
}

// ─── 섹션 2: 트렌드 + 버블 ──────────────────────────────────────────────────

/** 일별 기사 수 (analyzed 한정) */
export function buildDailyTrend(articles: AnalyzedArticle[]): DailyTrendPoint[] {
  const countMap = new Map<string, number>();

  for (const a of analyzed(articles)) {
    const date = toISODate(articleDate(a));
    countMap.set(date, (countMap.get(date) ?? 0) + 1);
  }

  return Array.from(countMap.entries())
    .filter(([date]) => date !== "unknown")
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }));
}

/** 키워드별 버블 클러스터 */
export function buildBubbleClusters(articles: AnalyzedArticle[]): BubbleCluster[] {
  const map = new Map<
    string,
    { dates: string[]; risks: number[]; domains: string[] }
  >();

  for (const a of analyzed(articles)) {
    for (const kw of a.keywords) {
      if (!map.has(kw)) map.set(kw, { dates: [], risks: [], domains: [] });
      const entry = map.get(kw)!;
      const iso = toISODate(articleDate(a));
      if (iso !== "unknown") entry.dates.push(iso);
      entry.risks.push(a.risk_score);
      entry.domains.push(...a.policy_domains);
    }
  }

  return Array.from(map.entries())
    .map(([keyword, { dates, risks, domains }]) => {
      const avgRisk = risks.length
        ? Math.round(risks.reduce((s, r) => s + r, 0) / risks.length)
        : 0;
      const firstDate = dates.sort()[0] ?? "";

      const domainCount = new Map<string, number>();
      for (const d of domains) domainCount.set(d, (domainCount.get(d) ?? 0) + 1);
      const dominantDomain =
        [...domainCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "";

      return { keyword, firstDate, avgRisk, count: risks.length, dominantDomain };
    })
    .filter((c) => c.count >= 1)
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .slice(0, 40);
}

// ─── 섹션 3: 키워드 + 타임라인 ──────────────────────────────────────────────

/** 키워드 빈도 (상위 30개) + 정책영역 색상 인코딩 */
export function buildKeywordFrequency(articles: AnalyzedArticle[]): KeywordFrequency[] {
  const freq = new Map<string, { count: number; domains: string[] }>();
  for (const a of analyzed(articles)) {
    for (const kw of a.keywords) {
      if (!freq.has(kw)) freq.set(kw, { count: 0, domains: [] });
      const entry = freq.get(kw)!;
      entry.count++;
      entry.domains.push(...a.policy_domains);
    }
  }
  return Array.from(freq.entries())
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 30)
    .map(([keyword, { count, domains }]): KeywordFrequency => {
      const domainCount = new Map<string, number>();
      for (const d of domains) domainCount.set(d, (domainCount.get(d) ?? 0) + 1);
      const topDomain = [...domainCount.entries()].sort((a, b) => b[1] - a[1])[0];
      const dominantDomain: string = topDomain ? topDomain[0] : "";
      return { keyword, count, dominantDomain };
    });
}

/** 고위험 이슈 (risk_score ≥ threshold, 내림차순, 상위 20건) */
export function getHighRiskIssues(
  articles: AnalyzedArticle[],
  threshold: number
): AnalyzedArticle[] {
  return analyzed(articles)
    .filter((a) => a.risk_score >= threshold)
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 20);
}

/** 특정 키워드가 포함된 기사 (리스크 내림차순, 상위 20건) */
export function getArticlesByKeyword(
  articles: AnalyzedArticle[],
  keyword: string
): AnalyzedArticle[] {
  return analyzed(articles)
    .filter((a) => a.keywords.includes(keyword))
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 20);
}

// ─── 섹션 4: 플랫폼 카드 ────────────────────────────────────────────────────

/** 플랫폼별 집계 카드 데이터 */
export function buildPlatformCards(articles: AnalyzedArticle[]): PlatformCard[] {
  const map = new Map<
    string,
    { risks: number[]; keywords: string[]; topEntry: { risk: number; summary: string } | null }
  >();

  for (const a of analyzed(articles)) {
    const ps = a.platforms.length > 0 ? a.platforms : ["기타"];
    for (const p of ps) {
      if (!map.has(p)) map.set(p, { risks: [], keywords: [], topEntry: null });
      const entry = map.get(p)!;
      entry.risks.push(a.risk_score);
      entry.keywords.push(...a.keywords);
      // 최고 리스크 기사의 요약만 보존
      if (a.summary && (!entry.topEntry || a.risk_score > entry.topEntry.risk)) {
        entry.topEntry = { risk: a.risk_score, summary: a.summary };
      }
    }
  }

  return Array.from(map.entries())
    .map(([platform, { risks, keywords, topEntry }]) => {
      const maxRisk = Math.max(...risks, 0);
      const avgRisk = risks.length
        ? Math.round(risks.reduce((s, r) => s + r, 0) / risks.length)
        : 0;

      const kwFreq = new Map<string, number>();
      for (const kw of keywords) kwFreq.set(kw, (kwFreq.get(kw) ?? 0) + 1);
      const topKeywords = [...kwFreq.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([kw]) => kw);

      return {
        platform,
        articleCount: risks.length,
        maxRisk,
        avgRisk,
        topKeywords,
        sampleSummary: topEntry?.summary ?? "",
      };
    })
    .sort((a, b) => b.maxRisk - a.maxRisk);
}

// ─── 섹션 4: 플랫폼 × 감성 ──────────────────────────────────────────────────

export interface PlatformSentimentStat {
  platform: string;
  긍정: number;
  부정: number;
  중립: number;
  total: number;
}

/** 플랫폼별 감성 분포 (기사 수 기준 상위 N개) */
export function buildPlatformSentimentStats(
  articles: AnalyzedArticle[],
  topN = 10
): PlatformSentimentStat[] {
  const map = new Map<string, { 긍정: number; 부정: number; 중립: number }>();

  for (const a of analyzed(articles)) {
    const ps = a.platforms.length > 0 ? a.platforms : ["기타"];
    for (const p of ps) {
      if (!map.has(p)) map.set(p, { 긍정: 0, 부정: 0, 중립: 0 });
      const entry = map.get(p)!;
      if (a.sentiment === "긍정") entry.긍정++;
      else if (a.sentiment === "부정") entry.부정++;
      else entry.중립++;
    }
  }

  return Array.from(map.entries())
    .map(([platform, counts]) => ({
      platform,
      ...counts,
      total: counts.긍정 + counts.부정 + counts.중립,
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, topN);
}

// ─── 색상 맵 ─────────────────────────────────────────────────────────────────

export const DOMAIN_COLORS: Record<string, string> = {
  "공정거래": "#3b82f6",
  "소비자보호": "#10b981",
  "개인정보": "#8b5cf6",
  "노동": "#f59e0b",
  "콘텐츠/저작권": "#ec4899",
  "안전": "#ef4444",
  "AI/자동화": "#06b6d4",
  "기타": "#6b7280",
};

export const SENTIMENT_COLORS: Record<string, string> = {
  "긍정": "#10b981",
  "부정": "#ef4444",
  "중립": "#94a3b8",
};

/** risk_score → 히트맵 셀 배경색 (dark mode inline style) */
export function riskToBgColor(score: number): string {
  if (score === 0) return "transparent";
  if (score < 20) return "rgba(30,58,138,0.35)";
  if (score < 40) return "rgba(30,58,138,0.65)";
  if (score < 60) return "rgba(113,63,18,0.70)";
  if (score < 75) return "rgba(124,45,18,0.75)";
  if (score < 90) return "rgba(127,29,29,0.85)";
  return "rgba(185,28,28,0.95)";
}

/** risk_score → Tailwind bg 클래스 (하위 호환) */
export function riskToTailwindBg(_score: number): string {
  return "";
}

/** 히트맵 셀 텍스트 색상 (다크모드 고정) */
export function riskToTextColor(): string {
  return "text-slate-200";
}

// ─── 섹션 1: 언론사 통계 (뉴스 기사 전용) ───────────────────────────────────

/** originallink에서 2-level 도메인 추출 (e.g. news.naver.com → naver.com) */
function extractDomain(url: string): string {
  try {
    const hostname = new URL(url).hostname.replace(/^www\./, "");
    const parts = hostname.split(".");
    return parts.length >= 2 ? parts.slice(-2).join(".") : hostname;
  } catch {
    return "";
  }
}

/** 뉴스 기사 언론사(도메인)별 기사 수 (상위 topN개 + 나머지 합산) */
export function buildMediaOutletStats(
  articles: AnalyzedArticle[],
  topN = 9
): MediaOutletCount[] {
  const freq = new Map<string, number>();

  for (const a of articles) {
    if (a.source_type !== "news") continue;
    const url = a.originallink ?? a.link ?? "";
    if (!url) continue;
    const domain = extractDomain(url);
    if (!domain) continue;
    freq.set(domain, (freq.get(domain) ?? 0) + 1);
  }

  const sorted = Array.from(freq.entries())
    .sort((a, b) => b[1] - a[1]);

  const top = sorted.slice(0, topN).map(([domain, count]) => ({ domain, count }));
  const rest = sorted.slice(topN).reduce((s, [, c]) => s + c, 0);
  if (rest > 0) top.push({ domain: "기타", count: rest });

  return top;
}
