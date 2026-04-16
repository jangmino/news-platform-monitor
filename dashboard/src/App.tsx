import { useMemo, useState } from "react";
import { useAnalysisData } from "@/hooks/useAnalysisData";
import { Section1Overview } from "@/components/Section1Overview";
import { Section2Trends } from "@/components/Section2Trends";
import { Section3Keywords } from "@/components/Section3Keywords";
import { Section4Platforms } from "@/components/Section4Platforms";
import { filterByDateRange } from "@/lib/dataUtils";
const DATE_RANGE_OPTIONS: { label: string; days: number | null }[] = [
  { label: "전체", days: null },
  { label: "최근 7일", days: 7 },
  { label: "최근 30일", days: 30 },
  { label: "최근 90일", days: 90 },
];

export default function App() {
  const {
    pressArticles,
    newsArticles,
    combinedRecs,
    pressRecs,
    pressGeneratedAt,
    newsGeneratedAt,
    isLoading,
    error,
  } = useAnalysisData();

  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<number | null>(null);

  const activeRecs = combinedRecs.length > 0 ? combinedRecs : pressRecs;

  const filteredArticles = useMemo(() => {
    const base = [...pressArticles, ...newsArticles];
    return filterByDateRange(base, dateRange);
  }, [pressArticles, newsArticles, dateRange]);

  const totalCount = pressArticles.length + newsArticles.length;
  const analyzedCount = filteredArticles.filter((a) => a.status === "analyzed").length;
  const isEmpty = totalCount === 0;

  // 가장 최근 생성 시각 표시
  const generatedAt = [pressGeneratedAt, newsGeneratedAt]
    .filter(Boolean)
    .sort()
    .at(-1) ?? "";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-muted-foreground">
        <div className="text-center space-y-2">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm">분석 데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-2">
          <p className="text-red-400 font-medium">데이터 로드 오류</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* 헤더 */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-lg font-bold text-foreground">KISDI 플랫폼 이슈 대시보드</h1>
            <p className="text-xs text-muted-foreground">디지털 플랫폼 정책 모니터링</p>
          </div>

          {!isEmpty && (
            <div className="flex items-center gap-3 flex-wrap">
              {/* 날짜 범위 필터 */}
              <div className="flex items-center gap-1 bg-slate-800/60 rounded-lg p-1">
                {DATE_RANGE_OPTIONS.map(({ label, days }) => (
                  <button
                    key={label}
                    onClick={() => setDateRange(days)}
                    className={`text-xs px-3 py-1.5 rounded-md transition-colors ${
                      dateRange === days
                        ? "bg-slate-600 text-white font-medium"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!isEmpty && (
            <div className="text-right text-xs text-muted-foreground">
              <p>{analyzedCount.toLocaleString()} / {totalCount.toLocaleString()}건 분석</p>
              {generatedAt && (
                <p>{new Date(generatedAt).toLocaleDateString("ko-KR")} 기준</p>
              )}
            </div>
          )}
        </div>
      </header>

      {/* 메인 */}
      <main className="max-w-screen-2xl mx-auto px-6 py-8">
        {isEmpty ? (
          <EmptyState />
        ) : (
          <div className="space-y-12">
            <Section1Overview
              articles={filteredArticles}
              totalCount={totalCount}
              analyzedCount={analyzedCount}
              generatedAt={generatedAt}
              recommendations={activeRecs}
              selectedPlatform={selectedPlatform}
              onPlatformSelect={setSelectedPlatform}
            />
            <hr className="border-slate-800" />
            <Section2Trends articles={filteredArticles} />
            <hr className="border-slate-800" />
            <Section3Keywords articles={filteredArticles} />
            <hr className="border-slate-800" />
            <Section4Platforms
              articles={filteredArticles}
              recommendations={activeRecs}
              selectedPlatform={selectedPlatform}
              onPlatformSelect={setSelectedPlatform}
            />
          </div>
        )}
      </main>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <div className="text-5xl">📊</div>
      <h2 className="text-xl font-semibold text-foreground">분석 데이터가 없습니다</h2>
      <p className="text-sm text-muted-foreground max-w-sm">
        먼저 Python 분석 파이프라인을 실행하세요.
      </p>
      <pre className="mt-2 px-4 py-3 bg-slate-800 rounded text-xs text-left font-mono text-slate-200">
        python -m src analyze-press{"\n"}python -m src analyze-news
      </pre>
      <p className="text-xs text-muted-foreground">
        완료 후 이 페이지를 새로고침하세요.
      </p>
    </div>
  );
}
