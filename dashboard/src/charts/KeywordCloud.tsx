import { DOMAIN_COLORS } from "@/lib/dataUtils";
import type { KeywordFrequency } from "@/types/analysis";

interface KeywordCloudProps {
  keywords: KeywordFrequency[];
  selectedKeyword?: string | null;
  onKeywordClick?: (keyword: string | null) => void;
}

const MIN_PX = 12;
const MAX_PX = 34;

export function KeywordCloud({ keywords, selectedKeyword, onKeywordClick }: KeywordCloudProps) {
  if (keywords.length === 0) {
    return (
      <div className="flex items-center justify-center h-[160px] text-muted-foreground text-sm">
        키워드 데이터 없음
      </div>
    );
  }

  const maxCount = keywords[0]?.count ?? 1;
  const minCount = keywords[keywords.length - 1]?.count ?? 1;
  const range = Math.max(maxCount - minCount, 1);

  function fontSize(count: number): number {
    return MIN_PX + Math.round(((count - minCount) / range) * (MAX_PX - MIN_PX));
  }

  function handleClick(keyword: string) {
    if (!onKeywordClick) return;
    onKeywordClick(selectedKeyword === keyword ? null : keyword);
  }

  const legendDomains = Object.entries(DOMAIN_COLORS);

  return (
    <div className="space-y-3">
      {/* 정책영역 색상 범례 */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-2 py-1.5 rounded bg-slate-900/40 border border-slate-800/60">
        <span className="text-[10px] text-slate-500 mr-1">정책영역</span>
        {legendDomains.map(([domain, color]) => (
          <div key={domain} className="flex items-center gap-1">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-[11px] text-slate-300">{domain}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2 items-baseline justify-center p-4 min-h-[160px]">
        {keywords.map(({ keyword, count, dominantDomain }) => {
        const color = DOMAIN_COLORS[dominantDomain] ?? DOMAIN_COLORS["기타"];
        const isSelected = selectedKeyword === keyword;
        const isOther = selectedKeyword && !isSelected;
        return (
          <span
            key={keyword}
            style={{
              fontSize: `${fontSize(count)}px`,
              color,
              lineHeight: 1.2,
              opacity: isOther ? 0.3 : 0.9,
              outline: isSelected ? `2px solid ${color}` : "none",
              outlineOffset: "2px",
              borderRadius: "3px",
              padding: isSelected ? "0 3px" : undefined,
              transition: "opacity 0.15s, outline 0.15s",
            }}
            title={`"${keyword}" — ${count}건 · ${dominantDomain || "미분류"}`}
            className={`font-medium select-none ${onKeywordClick ? "cursor-pointer" : "cursor-default"}`}
            onClick={() => handleClick(keyword)}
          >
            {keyword}
          </span>
        );
      })}
      </div>
    </div>
  );
}
