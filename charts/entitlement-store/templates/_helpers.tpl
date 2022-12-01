{{/*
Expand the name of the chart.
*/}}
{{- define "entitlement-store.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "entitlement-store.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "entitlement-store.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "entitlement-store.labels" -}}
helm.sh/chart: {{ include "entitlement-store.chart" . }}
{{ include "entitlement-store.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "entitlement-store.selectorLabels" -}}
app.kubernetes.io/name: {{ include "entitlement-store.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "entitlement-store.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "entitlement-store.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create OIDC Internal Url from a common value
*/}}
{{- define "entitlement-store.oidc.internalUrl" }}
{{- if .Values.oidc.internalHost }}
{{- .Values.oidc.internalHost }}
{{- else if .Values.global.opentdf.common.oidcUrlPath }}
{{- printf "%s/%s" .Values.global.opentdf.common.oidcInternalBaseUrl .Values.global.opentdf.common.oidcUrlPath }}
{{- else }}
{{- .Values.global.opentdf.common.oidcInternalBaseUrl }}
{{- end }}
{{- end }}


{{/*
Create OIDC External Url from a common value
*/}}
{{- define "entitlement-store.oidc.externalUrl" }}
{{- if .Values.oidc.externalHost }}
{{- .Values.oidc.externalHost }}
{{- else if .Values.global.opentdf.common.oidcUrlPath }}
{{- printf "%s/%s" .Values.global.opentdf.common.oidcExternalBaseUrl .Values.global.opentdf.common.oidcUrlPath }}
{{- else }}
{{- .Values.global.opentdf.common.oidcExternalBaseUrl }}
{{- end }}
{{- end }}
