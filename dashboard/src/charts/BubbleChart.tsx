import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { DOMAIN_COLORS } from "@/lib/dataUtils";
import type { BubbleCluster } from "@/types/analysis";

interface BubbleChartProps {
  clusters: BubbleCluster[];
}

interface Point {
  keyword: string;
  dominantDomain: string;
  x: number; // 출현 빈도 (기사 수)
  y: number; // 평균 리스크
  z: number; // 버블 크기 (출현 빈도)
  fill: string;
}

export function BubbleChart({ clusters }: BubbleChartProps) {
  if (clusters.length === 0) {
    return (
      <div className="flex items-center justify-center h-[220px] text-muted-foreground text-sm">
        클러스터 데이터 없음
      </div>
    );
  }

  const points: Point[] = clusters.map((c) => ({
    keyword: c.keyword,
    dominantDomain: c.dominantDomain,
    x: c.count,
    y: c.avgRisk,
    z: c.count,
    fill: DOMAIN_COLORS[c.dominantDomain] ?? DOMAIN_COLORS["기타"],
  }));

  const maxCount = Math.max(...points.map((p) => p.x));
  const midCount = Math.round(maxCount / 2);
  const midRisk = 50;

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ top: 8, right: 24, left: 0, bottom: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="x"
          type="number"
          name="출현 빈도"
          domain={[0, maxCount + 1]}
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          label={{ value: "출현 빈도 (건)", position: "insideBottom", offset: -12, fontSize: 11, fill: "#94a3b8" }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="평균 리스크"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          label={{ value: "리스크", angle: -90, position: "insideLeft", offset: 10, fontSize: 11, fill: "#94a3b8" }}
        />
        <ZAxis dataKey="z" range={[40, 500]} name="출현 빈도" />
        {/* 사분면 구분선 */}
        <ReferenceLine x={midCount} stroke="#475569" strokeDasharray="4 4" />
        <ReferenceLine y={midRisk} stroke="#475569" strokeDasharray="4 4" />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ payload }) => {
            if (!payload?.length) return null;
            const d = payload[0]?.payload as Point | undefined;
            if (!d) return null;
            return (
              <div className="bg-slate-800 border border-slate-600 rounded p-2 text-xs shadow text-slate-200">
                <p className="font-semibold text-white">{d.keyword}</p>
                <p className="text-slate-400">정책영역: {d.dominantDomain || "미분류"}</p>
                <p>출현 빈도: <span className="font-medium">{d.x}건</span></p>
                <p>평균 리스크: <span className="font-medium">{d.y}점</span></p>
              </div>
            );
          }}
        />
        <Scatter data={points} fillOpacity={0.75}>
          {points.map((p, i) => (
            <Cell key={i} fill={p.fill} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
