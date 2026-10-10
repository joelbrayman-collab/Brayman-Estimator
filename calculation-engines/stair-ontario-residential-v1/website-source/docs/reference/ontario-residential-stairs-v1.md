# Ontario Residential — V1 stair evidence record

Status: **Proposed — requires Joel's approval before implementation**  
Verified: **2026-09-26**  
Code edition: **2024 Ontario Building Code**  
Effective date used by this profile: **2025-01-01**

## Selected scope

This profile is deliberately limited to straight-flight **private stairs with rectangular treads** serving a house or an individual dwelling unit in Ontario. It evaluates only rise and run. The result will be presented as guidance against this named, dated profile—not as permit approval or a complete code review.

The Government of Ontario states that the 2024 Building Code came into effect on January 1, 2025. Ontario Regulation 163/24 adopts the National Building Code of Canada 2020 subject to Ontario's amendments. The official Ontario compendium and amendment record were checked for this evidence gate.

## Encoded limits

| Profile field | Value | Applicability | Source and reference |
| --- | ---: | --- | --- |
| `minRiserHeightMm` | 125 mm | Minimum rise for a private stair in the selected scope | NBC 2020, Division B, Sentence 9.8.4.1.(1), Table 9.8.4.1 |
| `maxRiserHeightMm` | 200 mm | Maximum rise for a private stair in the selected scope | NBC 2020, Division B, Sentence 9.8.4.1.(1), Table 9.8.4.1 |
| `minTreadRunMm` | 255 mm | Minimum run for a private stair with rectangular treads in the selected scope | 2024 OBC, Division B, Sentence 9.8.4.2.(1), Table 9.8.4.2; confirmed by City of Markham Builder Tip 106 |
| `maxTreadRunMm` | 355 mm | Maximum run for a private stair with rectangular treads in the selected scope | 2024 OBC, Division B, Sentence 9.8.4.2.(1), Table 9.8.4.2; confirmed by City of Markham Builder Tip 106 |

The Markham tip is dated January 1, 2025, identifies itself as updated to the 2024 OBC, and describes private stairs as including interior stairs within a house or individual dwelling unit. It also notes that rectangular tread depth must be at least the run and no more than the run plus 25 mm; tread depth is not encoded in this V1 profile.

## Sources

1. [The 2024 Ontario Building Code](https://www.ontario.ca/page/2024-ontario-building-code), Government of Ontario. Accessed 2026-09-26.
2. [Ontario Regulation 163/24 — Building Code](https://www.ontario.ca/laws/regulation/r24163), Government of Ontario. Accessed 2026-09-26.
3. [2024 Building Code Compendium](https://www.publications.gov.on.ca/store/20170501121/Free_Download_Files/301719.pdf), Publications Ontario, 2024 update containing O. Reg. 447/24. Accessed 2026-09-26.
4. [National Building Code of Canada 2020, Volume 2](https://publications.gc.ca/collections/collection_2022/cnrc-nrc/NR24-28-2020-eng.pdf), National Research Council Canada. Accessed 2026-09-26.
5. [Builder Tip No. 106 — Dimensions for Runs and Rectangular Treads — Housing](https://www.markham.ca/sites/default/files/2024-12/Builder%20Tip%20No.%20106%20-%20Dimensions%20For%20Runs%20And%20Rectangular%20Treads%20-%20Housing.pdf), City of Markham Building Standards, January 1, 2025. Accessed 2026-09-26.

## Excluded from V1 evaluation

The calculator may collect other dimensions for layout and material calculations, but this profile does **not** make a pass/fail statement about:

- stair width, total flight rise, landings, headroom, or doors;
- tread depth, nosings, uniformity tolerances, or slope;
- winders, tapered, curved, spiral, alternating-tread, or service stairs;
- guards, handrails, accessibility, fire exits, structural stringer design, or loading;
- exterior exposure details, public stairs, non-residential occupancies, existing-building Part 11 work, or local permit conditions.

The authority having jurisdiction, approved permit documents, and project professionals remain controlling. The profile must be re-verified when its code basis changes.

## Machine-readable evidence mirror

The build verifier compares this block exactly with the runtime profile. Do not edit one without the other.

<!-- profile-evidence:start -->
```json
{
  "id": "ontario-residential-v1",
  "codeEdition": "2024 Ontario Building Code",
  "effectiveDate": "2025-01-01",
  "verifiedAt": "2026-09-26",
  "limits": [
    {
      "field": "minRiserHeightMm",
      "value": 125,
      "unit": "mm",
      "applicability": "Minimum rise for a private stair in the selected residential scope.",
      "article": "Division B, Sentence 9.8.4.1.(1), Table 9.8.4.1",
      "sourceId": "nbc-2020"
    },
    {
      "field": "maxRiserHeightMm",
      "value": 200,
      "unit": "mm",
      "applicability": "Maximum rise for a private stair in the selected residential scope.",
      "article": "Division B, Sentence 9.8.4.1.(1), Table 9.8.4.1",
      "sourceId": "nbc-2020"
    },
    {
      "field": "minTreadRunMm",
      "value": 255,
      "unit": "mm",
      "applicability": "Minimum run for a private stair with rectangular treads in the selected residential scope.",
      "article": "Division B, Sentence 9.8.4.2.(1), Table 9.8.4.2",
      "sourceId": "markham-tip-106"
    },
    {
      "field": "maxTreadRunMm",
      "value": 355,
      "unit": "mm",
      "applicability": "Maximum run for a private stair with rectangular treads in the selected residential scope.",
      "article": "Division B, Sentence 9.8.4.2.(1), Table 9.8.4.2",
      "sourceId": "markham-tip-106"
    }
  ]
}
```
<!-- profile-evidence:end -->
