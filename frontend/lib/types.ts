export type ScenarioStatus = "not_started" | "active" | "closed";

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

export interface ScenarioInstance {
  id: string;
  cohort_id: string;
  student_id: string;
  status: ScenarioStatus;
  config: {
    artifacts?: ArtifactInject[];
    compliance_checklist?: ComplianceRule[];
    persona?: { system_prompt?: string; agenda?: string };
    [key: string]: unknown;
  };
  dataset_location: string | null;
  start_at: string | null;
  end_at: string | null;
  pivot_at: string | null;
  pivot_config: Record<string, unknown> | null;
  pivot_applied_at: string | null;
  notified_at: string | null;
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

export interface SubmissionResult {
  passed: boolean;
  failures: RuleFailure[];
}
