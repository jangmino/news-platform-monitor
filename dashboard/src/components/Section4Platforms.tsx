import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlatformSentimentBar } from "@/charts/PlatformSentimentBar";
import {
  buildPlatformCards,
  buildPlatformSentimentStats,
} from "@/lib/dataUtils";
import type { AnalyzedArticle, PolicyRecommendation, PlatformCard } from "@/types/analysis";

const DOMESTIC_PLATFORMS = new Set([
  "네이버", "카카오", "쿠팡", "배달의민족", "요기요", "당근", "토스",
  "야놀자", "무신사", "직방", "오늘의집", "카카오모빌리티", "네이버쇼핑",
]);
const FOREIGN_PLATFORMS = new Set([
  "구글", "유튜브", "메타", "인스타그램", "페이스북", "틱톡",
  "아마존", "테무", "알리익스프레스", "우버", "넷플릭스", "오픈AI",
]);

interface Section4PlatformsProps {
  articles: AnalyzedArticle[];
  recommendations: PolicyRecommendation[];
  selectedPlatform: string | null;
  onPlatformSelect: (platform: string | null) => void;
}

function riskStyle(score: number): { label: string; color: string; bg: string; border: string } {
  if (score >= 70) return { label: "고위험", color: "#ef4444", bg: "rgba(239,68,68,0.15)", border: "rgba(239,68,68,0.4)" };
  if (score >= 50) return { label: "주의",   color: "#f59e0b", bg: "rgba(245,158,11,0.15)", border: "rgba(245,158,11,0.4)" };
  return               { label: "관심",   color: "#64748b", bg: "rgba(100,116,139,0.15)", border: "rgba(100,116,139,0.3)" };
}

function platformGroup(platform: string): "domestic" | "foreign" | "other" {
  if (DOMESTIC_PLATFORMS.has(platform)) return "domestic";
  if (FOREIGN_PLATFORMS.has(platform)) return "foreign";
  return "other";
}

export function Section4Platforms({
  articles,
  recommendations,
  selectedPlatform,
  onPlatformSelect,
}: Section4PlatformsProps) {
  const allCards = buildPlatformCards(articles);
  const sentimentStats = buildPlatformSentimentStats(articles, 7);

  const cards = selectedPlatform
    ? allCards.filter((c) => c.platform === selectedPlatform)
    : allCards;

  const domesticCards = cards.filter((c) => platformGroup(c.platform) === "domestic");
  const foreignCards = cards.filter((c) => platformGroup(c.platform) === "foreign");
  const otherCards = cards.filter((c) => platformGroup(c.platform) === "other");

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-bold">섹션 4 · 플랫폼별 이슈 · AI 정책 제언</h2>
        {selectedPlatform && (
          <button
            onClick={() => onPlatformSelect(null)}
            className="text-xs text-blue-400 underline hover:no-underline"
          >
            필터 해제 ({selectedPlatform})
          </button>
        )}
      </div>

      {/* 플랫폼 × 감성 스택바 */}
      {!selectedPlatform && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">플랫폼별 감성 분포</CardTitle>
            <p className="text-xs text-muted-foreground">기사 수 상위 플랫폼 · 감성 비율(%) 비교</p>
          </CardHeader>
          <CardContent>
            <PlatformSentimentBar data={sentimentStats} />
          </CardContent>
        </Card>
      )}

      {/* 플랫폼 카드 그리드 (국내/해외 구분) */}
      {cards.length > 0 ? (
        <div className="space-y-6">
          {domesticCards.length > 0 && (
            <PlatformGroup
              label="국내 플랫폼"
              cards={domesticCards}
            />
          )}
          {foreignCards.length > 0 && (
            <PlatformGroup
              label="해외 플랫폼"
              cards={foreignCards}
            />
          )}
          {otherCards.length > 0 && (
            <PlatformGroup
              label="기타"
              cards={otherCards}
            />
          )}
        </div>
      ) : (
        <div className="text-center py-12 text-muted-foreground text-sm">
          {selectedPlatform
            ? `"${selectedPlatform}" 플랫폼의 분석 데이터가 없습니다.`
            : "플랫폼 데이터 없음"}
        </div>
      )}

      {/* AI 정책 제언 패널 */}
      {recommendations.length > 0 && (
        <div>
          <h3 className="text-base font-semibold mb-3">AI 정책 제언</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendations.map((rec, i) => (
              <Card key={i} className="border-blue-800 bg-blue-950/30">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex-none w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <CardTitle className="text-sm text-blue-200">{rec.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-blue-300 leading-relaxed">{rec.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function PlatformCardItem({ card }: { card: PlatformCard }) {
  const [expanded, setExpanded] = useState(false);
  const rs = riskStyle(card.avgRisk);
  const keywords = card.topKeywords.filter(
    (kw) => kw.toLowerCase() !== card.platform.toLowerCase()
  );

  return (
    <Card className="flex flex-col overflow-hidden">
      {/* 위험도 색상 상단 바 */}
      <div className="h-1 w-full" style={{ backgroundColor: rs.color, opacity: 0.7 }} />
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{card.platform}</CardTitle>
          <span
            className="shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full"
            style={{ color: rs.color, backgroundColor: rs.bg, border: `1px solid ${rs.border}` }}
          >
            평균 리스크 {card.avgRisk}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {card.articleCount}건 · 최고 {card.maxRisk}점
        </p>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="flex flex-wrap gap-1">
          {keywords.map((kw) => (
            <span
              key={kw}
              className="inline-block px-1.5 py-0.5 bg-blue-900/50 text-blue-300 rounded text-[11px]"
            >
              {kw}
            </span>
          ))}
        </div>
        {card.sampleSummary && (
          <div className="border-l-2 border-border pl-2">
            <p className={`text-xs text-muted-foreground ${expanded ? "" : "line-clamp-3"}`}>
              {card.sampleSummary}
            </p>
            <button
              onClick={() => setExpanded((v) => !v)}
              className="mt-1 text-[11px] text-blue-400 hover:text-blue-300"
            >
              {expanded ? "접기 ↑" : "더 보기 ↓"}
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PlatformGroup({ label, cards }: { label: string; cards: PlatformCard[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-slate-500" />
        {label}
        <span className="text-xs font-normal">({cards.length}개)</span>
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {cards.map((card) => (
          <PlatformCardItem key={card.platform} card={card} />
        ))}
      </div>
    </div>
  );
}
