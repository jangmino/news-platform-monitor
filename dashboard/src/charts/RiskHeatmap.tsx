import { riskToBgColor, riskToTextColor } from "@/lib/dataUtils";
import type { HeatmapCell } from "@/types/analysis";

interface RiskHeatmapProps {
  cells: HeatmapCell[];
  platforms: string[];
  domains: string[];
  selectedPlatform: string | null;
  onPlatformSelect: (platform: string | null) => void;
}

export function RiskHeatmap({
  cells,
  platforms,
  domains,
  selectedPlatform,
  onPlatformSelect,
}: RiskHeatmapProps) {
  const allDomains = [...domains, "기타"];

  // 모든 도메인에서 count=0인 플랫폼 제거
  const activePlatforms = [...platforms, "기타"].filter((platform) =>
    allDomains.some(
      (domain) => cells.find((c) => c.platform === platform && c.domain === domain && c.count > 0)
    )
  );
  const allPlatforms = activePlatforms;

  function getCell(platform: string, domain: string): HeatmapCell {
    return (
      cells.find((c) => c.platform === platform && c.domain === domain) ?? {
        platform,
        domain,
        avgRisk: 0,
        count: 0,
      }
    );
  }

  function handleCellClick(platform: string) {
    onPlatformSelect(selectedPlatform === platform ? null : platform);
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left font-medium text-muted-foreground w-24 min-w-[6rem]">
              플랫폼 ↓ / 정책영역 →
            </th>
            {allDomains.map((d) => (
              <th
                key={d}
                className="p-2 text-center font-medium text-muted-foreground whitespace-nowrap"
              >
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {allPlatforms.map((platform) => {
            const isSelected = selectedPlatform === platform;
            return (
              <tr
                key={platform}
                className={isSelected ? "ring-2 ring-inset ring-blue-400" : ""}
              >
                <td
                  className={`p-2 font-medium whitespace-nowrap cursor-pointer select-none
                    ${isSelected ? "text-blue-400 bg-blue-950/40" : "text-foreground hover:bg-muted"}`}
                  onClick={() => handleCellClick(platform)}
                  title={`${platform} 클릭하여 필터`}
                >
                  {platform}
                </td>
                {allDomains.map((domain) => {
                  const cell = getCell(platform, domain);
                  const textColor = riskToTextColor();
                  return (
                    <td
                      key={domain}
                      className={`p-2 text-center cursor-pointer select-none transition-colors hover:opacity-80 ${textColor}`}
                      style={{ backgroundColor: riskToBgColor(cell.avgRisk) }}
                      onClick={() => handleCellClick(platform)}
                      title={`${platform} × ${domain}: 평균 리스크 ${cell.avgRisk} (${cell.count}건)`}
                    >
                      {cell.count > 0 ? (
                        <span className="font-semibold">{cell.avgRisk}</span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted-foreground">
        셀 값: 평균 리스크 점수 (0–100) · 플랫폼 행 클릭 시 섹션 4 필터 적용
      </p>
    </div>
  );
}
