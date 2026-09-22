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

// FDE-013: a scenario can require a real, auto-graded deliverable instead
// of grading submission text by keyword alone -- a read-only SQL query
// (v1), or FDE-016's python_script (a data-cleaning script, run in a
// sandbox and compared to a reference solution's own output). The answer
// key (reference_query / reference_solution) is never sent to a student's
// browser -- the backend redacts it from every scenario-instance response
// (see backend/app/routers/scenario_instances.py); it only appears in the
// generator's own draft-preview response, an instructor-only step before
// an instance is even created, which is why both fields are optional here.
export interface SqlQueryTask {
  task_type: "sql_query";
  table_name: string;
  instructions?: string;
  compare?: "unordered_rows" | "ordered_rows";
  reference_query?: string;
}

export interface PythonScriptTask {
  task_type: "python_script";
  input_filename: string;
  output_filename: string;
  instructions?: string;
  compare?: "unordered_rows" | "exact";
  reference_solution?: string;
}

export type TechnicalTask = SqlQueryTask | PythonScriptTask;

// FDE-014: full scenario config the generator drafts from a raw requirement
// -- the same shape POST /scenario-instances' config accepts. Never carries
// compliance_checklist: a submission's whole content is the SQL query, so a
// prose-phrasing rule on that same field couldn't be jointly satisfiable
// with a working query (see backend/app/scenario_generator.py).
export interface GeneratedScenarioConfig {
  persona: { system_prompt: string; agenda: string };
  data_gen: { domain: string; messiness: "low" | "medium" | "high" };
  technical_task: TechnicalTask;
  legacy_system?: LegacySystemConfig;
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
    technical_task?: TechnicalTask;
    data_gen?: { domain: string; messiness: "low" | "medium" | "high"; row_count?: number };
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
  // FDE-017: set only when this instance is one stage of a multi-stage
  // Engagement rather than a standalone scenario -- both null together for
  // a standalone instance.
  engagement_id: string | null;
  stage_order: number | null;
}

export type EngagementStatus = "active" | "completed";

// FDE-017: a chain of ordered ScenarioInstance stages that together form
// one continuous, multi-stage engagement. `context` accumulates each
// approved stage's output (keyed by stage order as a string), merged into
// the next stage's config["engagement_context"] on advance.
export interface Engagement {
  id: string;
  cohort_id: string;
  student_id: string;
  status: EngagementStatus;
  context: Record<string, { submission_content: string | null; grading_result: unknown }>;
  created_at: string;
  completed_at: string | null;
  stages: ScenarioInstance[];
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
  grading_result: { task_type: string; passed: boolean } | null;
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
  grading_result: { task_type: string; passed: boolean } | null;
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

// FDE-015: lets a student browse the actual dataset before writing a query
// against it, instead of guessing at column names blind.
export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
}

// FDE-015: a non-graded "try it" run of a technical-task query -- the
// actual result set, not a pass/fail.
export interface QueryRunResult {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  truncated: boolean;
}

export interface SubmissionResult {
  passed: boolean;
  failures: RuleFailure[];
  // Present once the submission has actually been recorded on the backend's
  // approval workflow (FDE-007) — only happens when passed is true.
  submission?: SubmissionRecord;
}
