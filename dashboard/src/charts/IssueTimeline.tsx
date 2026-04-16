import type { AnalyzedArticle } from "@/types/analysis";

interface IssueTimelineProps {
  issues: AnalyzedArticle[];
  sortBy: "risk" | "date";
  onSortChange: (sort: "risk" | "date") => void;
  title?: string;
}

const SENTIMENT_STYLE: Record<string, string> = {
  부정: "bg-red-900/60 text-red-300",
  긍정: "bg-green-900/60 text-green-300",
  중립: "bg-slate-700 text-slate-300",
};

const SOURCE_STYLE: Record<string, string> = {
  press: "bg-blue-900/60 text-blue-300",
  news: "bg-green-900/60 text-green-300",
};

function riskBadge(score: number): string {
  if (score >= 80) return "bg-red-600 text-white";
  if (score >= 60) return "bg-orange-600 text-white";
  if (score >= 40) return "bg-yellow-600 text-white";
  return "bg-slate-600 text-slate-200";
}

function articleDateStr(issue: AnalyzedArticle): string {
  const ds = issue.date ?? issue.published_at ?? "";
  if (!ds) return "—";
  const d = new Date(ds);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("ko-KR", { month: "2-digit", day: "2-digit" });
}

function articleLink(issue: AnalyzedArticle): string | undefined {
  return issue.originallink ?? issue.link ?? undefined;
}

export function IssueTimeline({ issues, sortBy, onSortChange, title }: IssueTimelineProps) {
  const sorted = [...issues].sort((a, b) => {
    if (sortBy === "date") {
      const ds = (a.date ?? a.published_at) ?? "";
      const dt = (b.date ?? b.published_at) ?? "";
      return new Date(dt).getTime() - new Date(ds).getTime();
    }
    return b.risk_score - a.risk_score;
  });

  return (
    <div>
      {/* 헤더 + 정렬 토글 */}
      <div className="flex items-center justify-between mb-2">
        {title && <p className="text-xs text-muted-foreground">{title}</p>}
        <div className="flex items-center gap-1 ml-auto">
          <span className="text-xs text-muted-foreground mr-1">정렬:</span>
          <button
            onClick={() => onSortChange("risk")}
            className={`text-xs px-2 py-0.5 rounded transition-colors ${
              sortBy === "risk"
                ? "bg-slate-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            리스크순
          </button>
          <button
            onClick={() => onSortChange("date")}
            className={`text-xs px-2 py-0.5 rounded transition-colors ${
              sortBy === "date"
                ? "bg-slate-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            날짜순
          </button>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="flex items-center justify-center h-[160px] text-muted-foreground text-sm">
          해당 이슈 없음
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="py-2 px-3 text-left text-muted-foreground font-medium w-20">날짜</th>
                <th className="py-2 px-3 text-center text-muted-foreground font-medium w-14">출처</th>
                <th className="py-2 px-3 text-left text-muted-foreground font-medium">제목</th>
                <th className="py-2 px-3 text-center text-muted-foreground font-medium w-16">리스크</th>
                <th className="py-2 px-3 text-center text-muted-foreground font-medium w-14">감성</th>
                <th className="py-2 px-3 text-left text-muted-foreground font-medium w-28">정책영역</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((issue, i) => {
                const href = articleLink(issue);
                return (
                  <tr key={`${href ?? issue.title}-${i}`} className="border-b border-slate-800 hover:bg-slate-800/40">
                    <td className="py-2 px-3 text-muted-foreground whitespace-nowrap">
                      {articleDateStr(issue)}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] ${SOURCE_STYLE[issue.source_type] ?? SOURCE_STYLE["press"]}`}>
                        {issue.source_type === "news" ? "뉴스" : "보도자료"}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      {href ? (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 hover:underline line-clamp-2"
                        >
                          {issue.title}
                        </a>
                      ) : (
                        <span className="line-clamp-2 text-slate-300">{issue.title}</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded font-bold ${riskBadge(issue.risk_score)}`}>
                        {issue.risk_score}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] ${SENTIMENT_STYLE[issue.sentiment] ?? SENTIMENT_STYLE["중립"]}`}>
                        {issue.sentiment}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex flex-wrap gap-1">
                        {issue.policy_domains.slice(0, 2).map((d) => (
                          <span key={d} className="inline-block px-1.5 py-0.5 bg-blue-900/50 text-blue-300 rounded text-[10px]">
                            {d}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
