import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { DailyTrendPoint } from "@/types/analysis";

interface TrendChartProps {
  data: DailyTrendPoint[];
}

export function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[220px] text-muted-foreground text-sm">
        트렌드 데이터 없음
      </div>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    label: d.date.length >= 10 ? d.date.slice(5, 10) : d.date,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={formatted} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          interval="preserveStartEnd"
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
          formatter={(value: number) => [`${value}건`, "기사 수"]}
          labelFormatter={(label) => `날짜: ${label}`}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#60a5fa"
          strokeWidth={2}
          dot={data.length <= 14}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
