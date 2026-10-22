import type { ConcreteSlabResult } from "./concrete-slab";

export type CalculationDownload = {
  calculation_result: ConcreteSlabResult;
  consumer_metadata: {
    project_reference_name: string;
    download_title: "Calculation Summary";
    saved_at: string;
  };
};

export function createCalculationDownload(
  result: ConcreteSlabResult,
  projectReferenceName: string,
  savedAt: string,
): CalculationDownload {
  return {
    calculation_result: result,
    consumer_metadata: {
      project_reference_name: projectReferenceName.trim(),
      download_title: "Calculation Summary",
      saved_at: savedAt,
    },
  };
}

export function calculationDownloadFilename(projectReferenceName: string): string {
  const safeReference = projectReferenceName
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `${safeReference || "concrete-slab"}-calculation.json`;
}
