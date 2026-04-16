import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskHeatmap } from "@/charts/RiskHeatmap";
import { DomainBarChart } from "@/charts/DomainBarChart";
import { SentimentDonut } from "@/charts/SentimentDonut";
import { buildHeatmapMatrix, buildDomainStats, buildSentimentStats } from "@/lib/dataUtils";
import type { AnalyzedArticle, PolicyRecommendation } from "@/types/analysis";

const PLATFORMS = [
  "네이버", "카카오", "쿠팡", "배달의민족", "요기요", "당근", "토스",
  "야놀자", "무신사", "직방", "오늘의집", "카카오모빌리티", "네이버쇼핑",
  "구글", "유튜브", "메타", "인스타그램", "페이스북", "틱톡",
  "아마존", "테무", "알리익스프레스", "우버", "넷플릭스", "오픈AI",
];

const DOMAINS = [
  "공정거래", "소비자보호", "개인정보", "노동",
  "콘텐츠/저작권", "안전", "AI/자동화",
];

const RISK_THRESHOLD = 70;

interface Section1OverviewProps {
  articles: AnalyzedArticle[];
  totalCount: number;
  analyzedCount: number;
  generatedAt: string;
  recommendations: PolicyRecommendation[];
  selectedPlatform: string | null;
  onPlatformSelect: (platform: string | null) => void;
}

export function Section1Overview({
  articles,
  totalCount,
  analyzedCount,
  generatedAt,
  selectedPlatform,
  onPlatformSelect,
}: Section1OverviewProps) {
  const analyzed = articles.filter((a) => a.status === "analyzed");
  const avgRisk = analyzed.length
    ? Math.round(analyzed.reduce((s, a) => s + a.risk_score, 0) / analyzed.length)
    : 0;
  const highRiskCount = analyzed.filter((a) => a.risk_score >= RISK_THRESHOLD).length;

  const cells = buildHeatmapMatrix(articles, PLATFORMS, DOMAINS);
  const domainStats = buildDomainStats(articles);
  const sentimentStats = buildSentimentStats(articles);

  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })
    : "—";

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">섹션 1 · 데이터 개요</h2>
        <span className="text-xs text-muted-foreground">분석 기준: {formattedDate}</span>
      </div>

      {/* 요약 카드 4개 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="전체 보도자료" value={totalCount} unit="건" />
        <StatCard title="분석 완료" value={analyzedCount} unit="건" />
        <StatCard title="평균 리스크" value={avgRisk} unit="점" highlight={avgRisk >= RISK_THRESHOLD} />
        <StatCard title="고위험 이슈" value={highRiskCount} unit="건" highlight={highRiskCount > 0} />
      </div>

      {/* 정책영역 바차트 + 감성 도넛 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">정책영역별 기사 수</CardTitle>
            <p className="text-xs text-muted-foreground">색상 = 정책영역 구분</p>
          </CardHeader>
          <CardContent>
            <DomainBarChart data={domainStats} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">감성 분포</CardTitle>
            <p className="text-xs text-muted-foreground">분석 완료 기사 기준</p>
          </CardHeader>
          <CardContent>
            <SentimentDonut data={sentimentStats} />
          </CardContent>
        </Card>
      </div>

      {/* 리스크 히트맵 */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">리스크 히트맵 (플랫폼 × 정책영역)</CardTitle>
        </CardHeader>
        <CardContent>
          <RiskHeatmap
            cells={cells}
            platforms={PLATFORMS}
            domains={DOMAINS}
            selectedPlatform={selectedPlatform}
            onPlatformSelect={onPlatformSelect}
          />
        </CardContent>
      </Card>

    </section>
  );
}

function StatCard({
  title,
  value,
  unit,
  highlight = false,
}: {
  title: string;
  value: number;
  unit: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? "border-red-800" : ""}>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className={`text-3xl font-bold mt-1 ${highlight ? "text-red-400" : "text-foreground"}`}>
          {value.toLocaleString()}
          <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
        </p>
      </CardContent>
    </Card>
  );
}

export { PLATFORMS, DOMAINS, RISK_THRESHOLD };
