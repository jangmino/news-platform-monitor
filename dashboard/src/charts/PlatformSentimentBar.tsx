import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { SENTIMENT_COLORS } from "@/lib/dataUtils";
import type { PlatformSentimentStat } from "@/lib/dataUtils";

interface PlatformSentimentBarProps {
  data: PlatformSentimentStat[];
}

export function PlatformSentimentBar({ data }: PlatformSentimentBarProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-muted-foreground text-sm">
        플랫폼 감성 데이터 없음
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="platform"
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "12px",
          }}
          formatter={(value: number, name: string) => [`${value}건`, name]}
        />
        <Legend
          wrapperStyle={{ fontSize: "12px", color: "#94a3b8", paddingTop: "8px" }}
        />
        <Bar dataKey="부정" stackId="a" fill={SENTIMENT_COLORS["부정"]} fillOpacity={0.85} />
        <Bar dataKey="중립" stackId="a" fill={SENTIMENT_COLORS["중립"]} fillOpacity={0.85} />
        <Bar dataKey="긍정" stackId="a" fill={SENTIMENT_COLORS["긍정"]} fillOpacity={0.85} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
