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