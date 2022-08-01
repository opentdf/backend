{{/*
Expand the name of the chart.
*/}}
{{- define "backend.name" -}}
{{- default .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "backend.fullname" -}}
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
{{- define "backend.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create Keycloak External Url   
*/}}
{{- define "backend.keycloak.externalUrl" }}
{{- if .Values.global.opentdf.common.oidcUrlPath }}
{{- printf "%s/%s" .Values.global.opentdf.common.oidcExternalHost .Values.global.opentdf.common.oidcUrlPath }}
{{- else }}
{{- default .Values.global.opentdf.common.oidcExternalHost }}
{{- end }}
{{- end }}

{{- define "backend.secretFromConfig" -}}
{{- if not .root.Values.secrets.kas.external }}
{{- if eq .config.type "file"}}
{{- default ( .root.Files.Get .config.value ) | b64enc }}
{{- else }}
{{- default .config.value | b64enc }}
{{- end }}
{{- else }}
{{- default "" }}
{{- end }}
{{- end -}}

{{- define "backend.kas.ATTR_AUTHORITY_CERTIFICATE" }}
{{- default ( include "backend.secretFromConfig" (dict "root" . "config" .Values.secrets.kas.attrAuthorityCert ) ) }}
{{- end }}

{{- define "backend.kas.KAS_EC_SECP256R1_CERTIFICATE" }}
{{- default ( include "backend.secretFromConfig" (dict "root" . "config" .Values.secrets.kas.ecCert ) ) }}
{{- end }}

{{- define "backend.kas.KAS_CERTIFICATE" }}
{{- default ( include "backend.secretFromConfig" (dict "root" . "config" .Values.secrets.kas.cert ) ) }}
{{- end }}

{{- define "backend.kas.KAS_EC_SECP256R1_PRIVATE_KEY" }}
{{- default ( include "backend.secretFromConfig" (dict "root" . "config" .Values.secrets.kas.ecPrivKey ) ) }}
{{- end }}

{{- define "backend.kas.KAS_PRIVATE_KEY" }}
{{- default ( include "backend.secretFromConfig" (dict "root" . "config" .Values.secrets.kas.privKey ) ) }}
{{- end }}
