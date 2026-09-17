import type { ComplianceRule, RuleFailure, SubmissionResult } from "./types";

/**
 * Stand-in for the backend compliance check (see implementation log in
 * stories/FDE-008-student-workspace.md — mocks/compliance-engine exists only
 * as a bare Python library today, with no HTTP surface for the backend to
 * expose). Mirrors the same shape a real `POST .../submissions` response
 * would use, so swapping to a real backend endpoint later is a drop-in
 * change requiring no UI updates.
 */
export function evaluateSubmission(content: string, rules: ComplianceRule[]): SubmissionResult {
  const failures: RuleFailure[] = [];

  for (const rule of rules) {
    const ok = checkRule(content, rule);
    if (!ok) failures.push({ rule_id: rule.id, description: rule.description });
  }

  return { passed: failures.length === 0, failures };
}

function checkRule(content: string, rule: ComplianceRule): boolean {
  switch (rule.check) {
    case "must_include":
      return content.toLowerCase().includes(String(rule.value).toLowerCase());
    case "must_exclude":
      return !content.toLowerCase().includes(String(rule.value).toLowerCase());
    case "min_length":
      return content.length >= Number(rule.value);
    default:
      return true;
  }
}
