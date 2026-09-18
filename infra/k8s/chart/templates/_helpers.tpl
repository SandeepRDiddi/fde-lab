{{/*
Cohort id, normalized into a valid DNS-1123 label fragment. Fails fast
instead of silently provisioning a shared/ambiguous namespace when the
caller forgets --set cohortId=... (see infra/k8s/provision_cohort.py, the
only intended caller).
*/}}
{{- define "cohort.slug" -}}
{{- if not .Values.cohortId -}}
{{ fail "cohortId is required, e.g. --set cohortId=acme-univ-cs101-fall26" }}
{{- end -}}
{{- .Values.cohortId | lower | regexReplaceAll "[^a-z0-9-]+" "-" | trunc 53 | trimSuffix "-" -}}
{{- end -}}

{{/* "cohort-<slug>" -- namespace name and Helm release name are the same string by convention. */}}
{{- define "cohort.namespace" -}}
cohort-{{ include "cohort.slug" . }}
{{- end -}}

{{- define "cohort.labels" -}}
app.kubernetes.io/part-of: fde-lab
app.kubernetes.io/managed-by: {{ .Release.Service }}
fde-lab/cohort-id: {{ include "cohort.slug" . }}
{{- end -}}

{{/* Same connection-string shape as infra/docker-compose.yml's FDE_DATABASE_URL,
just pointed at the in-namespace postgres Service instead of the compose service name. */}}
{{- define "cohort.databaseUrl" -}}
postgresql+psycopg2://{{ .Values.postgres.user }}:{{ .Values.postgres.password }}@postgres:5432/{{ .Values.postgres.db }}
{{- end -}}

{{- define "cohort.redisUrl" -}}
redis://redis:6379/0
{{- end -}}
