import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendChart } from "@/charts/TrendChart";
import { BubbleChart } from "@/charts/BubbleChart";
import { buildDailyTrend, buildBubbleClusters } from "@/lib/dataUtils";
import type { AnalyzedArticle } from "@/types/analysis";

interface Section2TrendsProps {
  articles: AnalyzedArticle[];
}

export function Section2Trends({ articles }: Section2TrendsProps) {
  const trend = buildDailyTrend(articles);
  const clusters = buildBubbleClusters(articles);

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-bold">섹션 2 · 이슈 트렌드</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">일별 보도자료 수</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart data={trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">이슈 클러스터 버블차트</CardTitle>
            <p className="text-xs text-muted-foreground">
              x=출현 빈도, y=평균 리스크, 크기=출현 빈도, 색=정책영역 · 우상단일수록 핵심 이슈
            </p>
          </CardHeader>
          <CardContent>
            <BubbleChart clusters={clusters} />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
