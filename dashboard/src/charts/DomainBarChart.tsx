import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { DOMAIN_COLORS } from "@/lib/dataUtils";
import type { DomainStat } from "@/lib/dataUtils";

interface DomainBarChartProps {
  data: DomainStat[];
}

export function DomainBarChart({ data }: DomainBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[200px] text-muted-foreground text-sm">
        정책영역 데이터 없음
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 48, left: 4, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          allowDecimals={false}
        />
        <YAxis
          type="category"
          dataKey="domain"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          width={80}
        />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.05)" }}
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "12px",
          }}
          formatter={(value: number, name: string) => [
            name === "count" ? `${value}건` : `${value}점`,
            name === "count" ? "기사 수" : "평균 리스크",
          ]}
          labelFormatter={(label) => `정책영역: ${label}`}
        />
        <Bar dataKey="count" radius={[0, 3, 3, 0]}>
          {data.map((entry) => (
            <Cell
              key={entry.domain}
              fill={DOMAIN_COLORS[entry.domain] ?? DOMAIN_COLORS["기타"]}
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
