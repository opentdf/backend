{{/*
Expand the name of the chart.
*/}}
{{- define "kas.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "kas.fullname" -}}
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
{{- define "kas.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kas.labels" -}}
helm.sh/chart: {{ include "kas.chart" . }}
{{ include "kas.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kas.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kas.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kas.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kas.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Create oidc endpoint from a common value
*/}}
{{- define "kas.oidcPubkeyEndpoint" }}
{{- $t := coalesce .Values.endpoints.oidcPubkeyEndpoint .Values.global.opentdf.common.oidcInternalBaseUrl }}
{{- tpl $t $ | nindent 16 }}
{{- end }}

{{- define "kas.secretName" -}}
{{- if .Values.externalSecretName }}
{{- .Values.externalSecretName }}
{{- else }}
{{- printf "%s-secrets" ( include "kas.name" . ) }}
{{- end }}
{{- end }}

{{- define "kas.secretFromString" -}}
{{- if and (not .root.Values.externalSecretName) .value }}
{{- b64enc .value }}
{{- else }}
{{- "" }}
{{- end }}
{{- end }}

{{- define "kas.ATTR_AUTHORITY_CERTIFICATE" }}
{{- dict "root" . "value" .Values.envConfig.attrAuthorityCert | include "kas.secretFromString" }}
{{- end }}

{{- define "kas.KAS_EC_SECP256R1_CERTIFICATE" }}
{{- dict "root" . "value" .Values.envConfig.ecCert | include "kas.secretFromString" }}
{{- end }}

{{- define "kas.KAS_CERTIFICATE" }}
{{- dict "root" . "value" .Values.envConfig.cert | include "kas.secretFromString" }}
{{- end }}

{{- define "kas.KAS_EC_SECP256R1_PRIVATE_KEY" }}
{{- dict "root" . "value" .Values.envConfig.ecPrivKey | include "kas.secretFromString" }}
{{- end }}

{{- define "kas.KAS_PRIVATE_KEY" }}
{{- dict "root" . "value" .Values.envConfig.privKey | include "kas.secretFromString" }}
{{- end }}