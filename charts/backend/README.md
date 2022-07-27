
Deploy Chart:

1. Update Dependencies: `helm dependency update`
1. Add Secrets: Current kas requires `kas-secrets` be created prior to chart install.
1. Install Chart: `helm upgarde --install backend -f values.yaml`