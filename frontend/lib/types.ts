export type ScenarioStatus = "not_started" | "active" | "closed";

export type ApprovalStatus = "submitted" | "pending_review" | "approved" | "rejected";

export interface ArtifactInject {
  id: string;
  type: string;
  title: string;
  body: string;
  from?: string;
  created_at?: string;
}

export interface ComplianceRule {
  id: string;
  description: string;
  check: "must_include" | "must_exclude" | "min_length";
  value: string | number;
}

export interface LegacySystemConfig {
  scenario_id: string;
  path: string;
  auth_header_name?: string;
  // Free-text hint for what this system is / why the student needs it --
  // shown in the panel alongside the query form.
  description?: string;
}

export interface ScenarioInstance {
  id: string;
  cohort_id: string;
  student_id: string;
  status: ScenarioStatus;
  config: {
    artifacts?: ArtifactInject[];
    compliance_checklist?: ComplianceRule[];
    persona?: { system_prompt?: string; agenda?: string };
    legacy_system?: LegacySystemConfig;
    [key: string]: unknown;
  };
  dataset_location: string | null;
  start_at: string | null;
  end_at: string | null;
  pivot_at: string | null;
  pivot_config: Record<string, unknown> | null;
  pivot_applied_at: string | null;
  notified_at: string | null;
  approval_outcome: ApprovalStatus | null;
  approval_decided_at: string | null;
  created_at: string;
}

export type MessageRole = "student" | "persona";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ConversationRead {
  scenario_instance_id: string;
  student_id: string;
  messages: Message[];
}

export interface RuleFailure {
  rule_id: string;
  description: string;
}

export interface SubmissionRecord {
  id: string;
  status: ApprovalStatus;
  review_deadline_at: string | null;
}

// Full shape of the backend's SubmissionRead (FDE-007) — the instructor
// console needs the submission content and decision detail that
// SubmissionRecord (the student submit-panel's narrower view) doesn't carry.
export interface SubmissionDetail {
  id: string;
  scenario_instance_id: string;
  content: string;
  status: ApprovalStatus;
  review_deadline_at: string | null;
  auto_decision: ApprovalStatus | null;
  decided_at: string | null;
  notified_at: string | null;
  created_at: string;
}

export interface ScenarioSchedule {
  start_at: string;
  end_at: string;
  pivot_at?: string | null;
  pivot_config?: Record<string, unknown> | null;
}

export interface SubmissionResult {
  passed: boolean;
  failures: RuleFailure[];
  // Present once the submission has actually been recorded on the backend's
  // approval workflow (FDE-007) — only happens when passed is true.
  submission?: SubmissionRecord;
}
