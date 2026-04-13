import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KeywordCloud } from "@/charts/KeywordCloud";
import { IssueTimeline } from "@/charts/IssueTimeline";
import {
  buildKeywordFrequency,
  getHighRiskIssues,
  getArticlesByKeyword,
} from "@/lib/dataUtils";
import { RISK_THRESHOLD } from "@/components/Section1Overview";
import type { AnalyzedArticle } from "@/types/analysis";

interface Section3KeywordsProps {
  articles: AnalyzedArticle[];
}

export function Section3Keywords({ articles }: Section3KeywordsProps) {
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"risk" | "date">("risk");

  const keywords = buildKeywordFrequency(articles);

  const issues = selectedKeyword
    ? getArticlesByKeyword(articles, selectedKeyword)
    : getHighRiskIssues(articles, RISK_THRESHOLD);

  const timelineTitle = selectedKeyword
    ? `"${selectedKeyword}" 관련 기사 (${issues.length}건)`
    : `고위험 이슈 (리스크 ${RISK_THRESHOLD}점 이상 · 상위 20건)`;

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-bold">섹션 3 · 키워드 · 이슈 타임라인</h2>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <CardTitle className="text-base">키워드 태그 클라우드</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                폰트 크기 = 출현 빈도 · 색상 = 정책영역 · 클릭하면 관련 기사 표시
              </p>
            </div>
            {selectedKeyword && (
              <button
                onClick={() => setSelectedKeyword(null)}
                className="text-xs text-blue-400 underline hover:no-underline shrink-0"
              >
                필터 해제
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <KeywordCloud
            keywords={keywords}
            selectedKeyword={selectedKeyword}
            onKeywordClick={setSelectedKeyword}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">이슈 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <IssueTimeline
            issues={issues}
            sortBy={sortBy}
            onSortChange={setSortBy}
            title={timelineTitle}
          />
        </CardContent>
      </Card>
    </section>
  );
}
