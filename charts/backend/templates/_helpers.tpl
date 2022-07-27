{{/*
Create Keycloak External Url   
*/}}
{{- define "backend.keycloak.externalUrl" }}
{{- if and ( .Values.global ) ( .Values.global.common ) ( .Values.global.common.oidcExternalHost ) }}
{{- if .Values.global.common.oidcUrlPath }}
{{- printf "%s/%s" .Values.global.common.oidcExternalHost .Values.global.common.oidcUrlPath }}
{{- else }}
{{- default .Values.global.common.oidcExternalHost }}
{{- end }}
{{- else }}
{{- default "" }}
{{- end }}
{{- end }}