{{- define "entity-resolution.imagePullSecret" }}
{{- with .Values.global.imageCredentials }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}

{{/*
Expand the name of the chart.
*/}}
{{- define "keycloak-bootstrap.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "keycloak-bootstrap.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "keycloak-bootstrap.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}


{{/*
Common labels
*/}}
{{- define "keycloak-bootstrap.labels" -}}
helm.sh/chart: {{ include "keycloak-bootstrap.chart" . }}
{{ include "keycloak-bootstrap.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "keycloak-bootstrap.selectorLabels" -}}
app.kubernetes.io/name: {{ include "keycloak-bootstrap.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create OIDC Internal Url from a common value (if it exists)
*/}}
{{- define "bootstrap.oidc.internalUrl" }}
{{- if .Values.keycloak.hostname }}
{{- .Values.keycloak.hostname }}
{{- else }}
{{- $host := .Values.global.opentdf.common.oidcInternalBaseUrl -}}
{{- if .Values.global.opentdf.common.oidcUrlPath }}
{{- printf "%s/%s" $host .Values.global.opentdf.common.oidcUrlPath }}
{{- else }}
{{- $host }}
{{- end }}
{{- end }}
{{- end }}

{{/*
The base URL for clients by default
*/}}
{{- define "bootstrap.opentdf.externalUrl" }}
{{- coalesce .Values.opentdf.externalUrl .Values.externalUrl .Values.global.opentdf.common.oidcExternalBaseUrl
  | required "Please define the abacus host URL for redirects" }}
{{- end }}

{{/*
Valid redirect URIs
*/}}
{{- define "bootstrap.opentdf.redirectUris" }}
{{- $defHost := coalesce .Values.opentdf.redirectUris }}
{{- join " " .Values.opentdf.redirectUris | default (printf "%s/*" $defHost) }}
{{- end }}
