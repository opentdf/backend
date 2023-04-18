{{/*
Backend Ingress gateway name
*/}}
{{- define "backend.ingress.gateway" -}}
{{- if .Values.global.opentdf.common.istio.ingress.existingGateway -}}
{{ .Values.global.opentdf.common.istio.ingress.existingGateway }}
{{- else -}}
{{ .Values.global.opentdf.common.istio.ingress.name }}
{{- end }}
{{- end }}
