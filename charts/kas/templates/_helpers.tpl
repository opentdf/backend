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
{{- default .Values.global.opentdf.common.oidcInternalBaseUrl }}
{{- end }}

{{- define "kas.secretName" -}}
{{- if .Values.externalSecretName }}
{{- default .Values.externalSecretName }}
{{- else }}
{{- printf "%s-secrets" ( include "kas.name" . ) }}
{{- end }}
{{- end }}

{{- define "kas.secretFromString" -}}
{{- if and (not .root.Values.externalEnvSecretName) (.value)  }}
{{- default .value | b64enc }}
{{- else }}
{{- default "" }}
{{- end }}
{{- end -}}

{{- define "kas.ATTR_AUTHORITY_CERTIFICATE" }}
{{- default ( include "kas.secretFromString" (dict "root" . "value" .Values.envConfig.attrAuthorityCert ) ) }}
{{- end }}

{{- define "kas.KAS_EC_SECP256R1_CERTIFICATE" }}
{{- default ( include "kas.secretFromString" (dict "root" . "value" .Values.envConfig.ecCert ) ) }}
{{- end }}

{{- define "kas.KAS_CERTIFICATE" }}
{{- default ( include "kas.secretFromString" (dict "root" . "value" .Values.envConfig.cert ) ) }}
{{- end }}

{{- define "kas.KAS_EC_SECP256R1_PRIVATE_KEY" }}
{{- default ( include "kas.secretFromString" (dict "root" . "value" .Values.envConfig.ecPrivKey ) ) }}
{{- end }}

{{- define "kas.KAS_PRIVATE_KEY" }}
{{- default ( include "kas.secretFromString" (dict "root" . "value" .Values.envConfig.privKey ) ) }}
{{- end }}