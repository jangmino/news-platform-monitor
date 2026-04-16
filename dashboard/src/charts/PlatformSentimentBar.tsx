import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import { SENTIMENT_COLORS } from "@/lib/dataUtils";
import type { PlatformSentimentStat } from "@/lib/dataUtils";

interface PlatformSentimentBarProps {
  data: PlatformSentimentStat[];
}

interface RowData {
  platform: string;
  total: number;
  긍정Pct: number;
  중립Pct: number;
  부정Pct: number;
  긍정Raw: number;
  중립Raw: number;
  부정Raw: number;
}

function toPercent(n: number, total: number) {
  return total === 0 ? 0 : Math.round((n / total) * 1000) / 10;
}

// 마지막 세그먼트 끝에 총 건수 표시
function TotalLabel(props: { x?: number; y?: number; width?: number; height?: number; value?: number }) {
  const { x = 0, y = 0, width = 0, height = 0, value } = props;
  if (!value) return null;
  return (
    <text
      x={x + width + 6}
      y={y + height / 2}
      dominantBaseline="central"
      fontSize={11}
      fill="#64748b"
    >
      {value}건
    </text>
  );
}

export function PlatformSentimentBar({ data }: PlatformSentimentBarProps) {
  // "기타" 제외 후 비율 변환
  const rows: RowData[] = data
    .filter((d) => d.platform !== "기타")
    .map((d) => ({
      platform: d.platform,
      total: d.total,
      긍정Pct: toPercent(d.긍정, d.total),
      중립Pct: toPercent(d.중립, d.total),
      부정Pct: toPercent(d.부정, d.total),
      긍정Raw: d.긍정,
      중립Raw: d.중립,
      부정Raw: d.부정,
    }));

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-muted-foreground text-sm">
        플랫폼 감성 데이터 없음
      </div>
    );
  }

  const chartHeight = Math.max(280, rows.length * 42 + 60);

  return (
    <div className="space-y-2">
      <p className="text-[11px] text-slate-500 px-1">* "기타"(미분류 플랫폼) 제외 · 비율 기준</p>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 72, left: 8, bottom: 24 }}
          barSize={20}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="platform"
            width={72}
            tick={{ fontSize: 12, fill: "#cbd5e1" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            content={({ payload, label }) => {
              if (!payload?.length) return null;
              const row = rows.find((r) => r.platform === label);
              if (!row) return null;
              return (
                <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs shadow-xl min-w-[160px]">
                  <p className="font-bold text-white text-sm mb-2">{label}</p>
                  <p className="text-slate-400 mb-1.5">총 {row.total}건</p>
                  <div className="space-y-1">
                    {[
                      { key: "긍정", raw: row.긍정Raw, pct: row.긍정Pct, color: SENTIMENT_COLORS["긍정"] },
                      { key: "중립", raw: row.중립Raw, pct: row.중립Pct, color: SENTIMENT_COLORS["중립"] },
                      { key: "부정", raw: row.부정Raw, pct: row.부정Pct, color: SENTIMENT_COLORS["부정"] },
                    ].map(({ key, raw, pct, color }) => (
                      <div key={key} className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-1.5">
                          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                          <span style={{ color }}>{key}</span>
                        </div>
                        <span className="text-white font-semibold">{pct}% <span className="text-slate-400 font-normal">({raw}건)</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }}
          />
          <Legend
            verticalAlign="bottom"
            wrapperStyle={{ fontSize: "12px", color: "#94a3b8", paddingTop: "12px" }}
            formatter={(value) => <span style={{ color: SENTIMENT_COLORS[value] ?? "#94a3b8" }}>{value}</span>}
          />
          <Bar dataKey="부정Pct" name="부정" stackId="s" fill={SENTIMENT_COLORS["부정"]} fillOpacity={0.85} />
          <Bar dataKey="중립Pct" name="중립" stackId="s" fill={SENTIMENT_COLORS["중립"]} fillOpacity={0.75} />
          <Bar dataKey="긍정Pct" name="긍정" stackId="s" fill={SENTIMENT_COLORS["긍정"]} fillOpacity={0.85} radius={[0, 3, 3, 0]}>
            <LabelList dataKey="total" content={<TotalLabel />} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
