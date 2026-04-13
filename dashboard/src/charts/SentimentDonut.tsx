import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { SENTIMENT_COLORS } from "@/lib/dataUtils";
import type { SentimentStat } from "@/lib/dataUtils";

interface SentimentDonutProps {
  data: SentimentStat[];
}

export function SentimentDonut({ data }: SentimentDonutProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[200px] text-muted-foreground text-sm">
        감성 데이터 없음
      </div>
    );
  }

  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="sentiment"
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={75}
          paddingAngle={3}
          label={({ sentiment, count }) =>
            `${sentiment} ${Math.round((count / total) * 100)}%`
          }
          labelLine={false}
        >
          {data.map((entry) => (
            <Cell
              key={entry.sentiment}
              fill={SENTIMENT_COLORS[entry.sentiment] ?? "#6b7280"}
              fillOpacity={0.85}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "12px",
          }}
          formatter={(value: number) => [
            `${value}건 (${Math.round((value / total) * 100)}%)`,
            "기사 수",
          ]}
        />
        <Legend
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: "12px" }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
