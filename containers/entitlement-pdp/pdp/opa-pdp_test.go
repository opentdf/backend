package pdp

import (
	"os"
	"strings"
	"testing"
)

func TestReplaceOpaEnvVar(t *testing.T) {
	os.Setenv("OPA_POLICYBUNDLE_PULLCRED", "myvalue")
	const configWithCrPat = "services:\n  policy-registry:\n    url: https://ghcr.io\n    type: oci\n    credentials:\n      bearer:\n        token: \"${CR_PAT}\""
	replaced := replaceOpaEnvVar([]byte(configWithCrPat))
	if strings.Contains(string(replaced), "${CR_PAT}") {
		t.Errorf("replacement failed: %s", replaced)
		t.Fail()
	}
}

func TestReplaceOpaEnvVarOpa(t *testing.T) {
	err := os.Setenv("OPA_POLICYBUNDLE_PULLCRED", "myvalue")
	if err != nil {
		t.Error(err)
	}
	const configWithPolCred = "services:\n  policy-registry:\n    url: https://ghcr.io\n    type: oci\n    credentials:\n      bearer:\n        token: \"${OPA_POLICYBUNDLE_PULLCRED}\""
	replaced := replaceOpaEnvVar([]byte(configWithPolCred))
	if strings.Contains(string(replaced), "${OPA_POLICYBUNDLE_PULLCRED}") {
		t.Errorf("replacement failed: %s", replaced)
		t.Fail()
	}
}

func TestReplaceOpaEnvVarNonOpa(t *testing.T) {
	os.Setenv("MY_SECRET", "myvalue")
	const configWithSECRET = "services:\n  policy-registry:\n    url: https://ghcr.io\n    type: oci\n    credentials:\n      bearer:\n        token: \"${MY_SECRET}\""
	replaced := replaceOpaEnvVar([]byte(configWithSECRET))
	if strings.Contains(string(replaced), "${MY_SECRET}") {
		return
	}
	t.Errorf("replacement unexpected: %s", replaced)
	t.Fail()
}
