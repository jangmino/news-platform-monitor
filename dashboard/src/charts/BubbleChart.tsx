import { DOMAIN_COLORS } from "@/lib/dataUtils";
import type { BubbleCluster } from "@/types/analysis";

interface BubbleChartProps {
  clusters: BubbleCluster[];
}

const RISK_LEVELS = [
  { min: 70, label: "고위험", color: "#ef4444", bg: "rgba(239,68,68,0.12)" },
  { min: 50, label: "주의",   color: "#f59e0b", bg: "rgba(245,158,11,0.10)" },
  { min: 0,  label: "관심",   color: "#3b82f6", bg: "rgba(59,130,246,0.08)" },
];

function riskLevel(score: number) {
  return RISK_LEVELS.find((r) => score >= r.min) ?? RISK_LEVELS[2];
}

export function BubbleChart({ clusters }: BubbleChartProps) {
  if (clusters.length === 0) {
    return (
      <div className="flex items-center justify-center h-[220px] text-muted-foreground text-sm">
        클러스터 데이터 없음
      </div>
    );
  }

  // avgRisk 내림차순 정렬, 상위 5개만
  const sorted = [...clusters].sort((a, b) => b.avgRisk - a.avgRisk).slice(0, 5);
  const maxRisk = 100;

  return (
    <div className="space-y-4">
      {/* 범례 */}
      <div className="flex flex-wrap items-center gap-4 px-1">
        <div className="flex gap-3">
          {RISK_LEVELS.map((r) => (
            <div key={r.label} className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: r.color }} />
              <span className="text-[11px] text-slate-400">{r.label} {r.label === "고위험" ? "≥70" : r.label === "주의" ? "50–69" : "<50"}</span>
            </div>
          ))}
        </div>
        <span className="text-[10px] text-slate-600 ml-auto">바 길이 = 리스크 점수 · 숫자 = 출현 건수</span>
      </div>

      {/* 키워드 리스크 바 */}
      <div className="space-y-2">
        {sorted.map((c) => {
          const level = riskLevel(c.avgRisk);
          const pct = (c.avgRisk / maxRisk) * 100;
          const domainColor = DOMAIN_COLORS[c.dominantDomain] ?? DOMAIN_COLORS["기타"];

          return (
            <div key={c.keyword} className="flex items-center gap-3">
              {/* 키워드명 */}
              <div className="w-28 shrink-0 text-right">
                <span className="text-xs text-slate-200 font-medium truncate block" title={c.keyword}>
                  {c.keyword}
                </span>
                <span
                  className="text-[10px] truncate block"
                  style={{ color: domainColor }}
                >
                  {c.dominantDomain || "미분류"}
                </span>
              </div>

              {/* 바 트랙 */}
              <div className="flex-1 relative h-7 rounded bg-slate-800/60">
                {/* 리스크 바 */}
                <div
                  className="absolute inset-y-0 left-0 rounded flex items-center pl-2 transition-all"
                  style={{
                    width: `${Math.max(pct, 4)}%`,
                    backgroundColor: level.bg,
                    borderLeft: `3px solid ${level.color}`,
                  }}
                >
                  <span
                    className="text-xs font-bold"
                    style={{ color: level.color }}
                  >
                    {c.avgRisk}
                  </span>
                </div>

                {/* 70점 기준선 */}
                <div
                  className="absolute inset-y-0 w-px bg-red-800/50"
                  style={{ left: "70%" }}
                />
              </div>

              {/* 출현 건수 뱃지 */}
              <div
                className="w-12 shrink-0 text-center text-[11px] font-semibold rounded px-1.5 py-0.5"
                style={{ color: domainColor, backgroundColor: `${domainColor}20` }}
              >
                {c.count}건
              </div>
            </div>
          );
        })}
      </div>

      {/* 기준선 범례 */}
      <div className="flex items-center gap-2 px-1 pt-1">
        <div className="h-px flex-1 bg-slate-800" />
        <span className="text-[10px] text-slate-600">▲ 바 길이가 길수록 높은 리스크</span>
        <div className="h-px flex-1 bg-slate-800" />
        <span className="text-[10px] text-red-900 flex items-center gap-1">
          <span className="inline-block w-px h-3 bg-red-800/60" />
          70점 기준
        </span>
      </div>
    </div>
  );
}
