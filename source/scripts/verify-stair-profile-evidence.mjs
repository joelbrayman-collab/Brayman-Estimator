import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const profilePath = path.join(
  projectRoot,
  "lib/useful-tools/profiles/ontario-residential-v1.json",
);
const evidencePath = path.join(
  projectRoot,
  "docs/reference/ontario-residential-stairs-v1.md",
);

function requireText(value, field) {
  assert.equal(typeof value, "string", `${field} must be a string`);
  assert.ok(value.trim(), `${field} must not be empty`);
}

function validateIsoDate(value, field) {
  requireText(value, field);
  assert.match(value, /^\d{4}-\d{2}-\d{2}$/, `${field} must use YYYY-MM-DD`);
  assert.ok(!Number.isNaN(Date.parse(`${value}T00:00:00Z`)), `${field} must be valid`);
}

function validateSources(sources) {
  assert.ok(Array.isArray(sources) && sources.length > 0, "sources must not be empty");
  const ids = new Set();
  for (const [index, source] of sources.entries()) {
    requireText(source.id, `sources[${index}].id`);
    assert.ok(!ids.has(source.id), `duplicate source id: ${source.id}`);
    ids.add(source.id);
    requireText(source.title, `sources[${index}].title`);
    requireText(source.publisher, `sources[${index}].publisher`);
    requireText(source.url, `sources[${index}].url`);
    validateIsoDate(source.accessedAt, `sources[${index}].accessedAt`);
  }
  return ids;
}

function validateLimits(limits, sourceIds, owner) {
  assert.ok(Array.isArray(limits) && limits.length > 0, `${owner}.limits must not be empty`);
  const fields = new Set();
  for (const [index, limit] of limits.entries()) {
    const prefix = `${owner}.limits[${index}]`;
    requireText(limit.field, `${prefix}.field`);
    assert.ok(!fields.has(limit.field), `duplicate limit field: ${limit.field}`);
    fields.add(limit.field);
    assert.equal(typeof limit.value, "number", `${prefix}.value must be numeric`);
    assert.ok(Number.isFinite(limit.value) && limit.value > 0, `${prefix}.value must be positive`);
    requireText(limit.unit, `${prefix}.unit`);
    requireText(limit.applicability, `${prefix}.applicability`);
    requireText(limit.article, `${prefix}.article`);
    requireText(limit.sourceId, `${prefix}.sourceId`);
    assert.ok(sourceIds.has(limit.sourceId), `${prefix}.sourceId must name a source`);
  }
}

export function verifyProfileEvidence(profile, evidence) {
  for (const field of ["id", "label", "codeEdition", "scope"]) {
    requireText(profile[field], `profile.${field}`);
  }
  validateIsoDate(profile.effectiveDate, "profile.effectiveDate");
  validateIsoDate(profile.verifiedAt, "profile.verifiedAt");
  const sourceIds = validateSources(profile.sources);
  validateLimits(profile.limits, sourceIds, "profile");

  assert.deepEqual(
    {
      id: evidence.id,
      codeEdition: evidence.codeEdition,
      effectiveDate: evidence.effectiveDate,
      verifiedAt: evidence.verifiedAt,
      limits: evidence.limits,
    },
    {
      id: profile.id,
      codeEdition: profile.codeEdition,
      effectiveDate: profile.effectiveDate,
      verifiedAt: profile.verifiedAt,
      limits: profile.limits,
    },
    "profile values must exactly match the evidence record",
  );

  return profile.limits.length;
}

async function main() {
  const [profileText, evidenceText] = await Promise.all([
    readFile(profilePath, "utf8"),
    readFile(evidencePath, "utf8"),
  ]);
  const profile = JSON.parse(profileText);
  const match = evidenceText.match(
    /<!-- profile-evidence:start -->\s*```json\s*([\s\S]*?)\s*```\s*<!-- profile-evidence:end -->/,
  );
  assert.ok(match, "evidence record must contain the machine-readable evidence block");
  const evidence = JSON.parse(match[1]);
  const count = verifyProfileEvidence(profile, evidence);
  console.log(
    `PASS ${profile.id} | ${profile.codeEdition} | effective ${profile.effectiveDate} | ${count} verified limits`,
  );
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`FAIL ${error.message}`);
    process.exitCode = 1;
  });
}
