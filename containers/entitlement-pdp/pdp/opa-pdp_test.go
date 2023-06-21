package pdp

import (
	"os"
	"strings"
	"testing"
)

func TestReplaceOpaEnvVar(t *testing.T) {
	os.Setenv("OPA_POLICYBUNDLE_PULLCRED", "myvalue")
	replaced := replaceOpaEnvVar([]byte(configWithCrPat))
	if strings.Contains(string(replaced), "${CR_PAT}") {
		t.Errorf("replacement failed: %s", replaced)
		t.Fail()
	}
}

func TestReplaceOpaEnvVarOpa(t *testing.T) {
	os.Setenv("OPA_POLICYBUNDLE_PULLCRED", "myvalue")
	replaced := replaceOpaEnvVar([]byte(configWithCrPat))
	if strings.Contains(string(replaced), "${OPA_POLICYBUNDLE_PULLCRED}") {
		t.Errorf("replacement failed: %s", replaced)
		t.Fail()
	}
}

func TestReplaceOpaEnvVarNonOpa(t *testing.T) {
	os.Setenv("MY_SECRET", "myvalue")
	replaced := replaceOpaEnvVar([]byte(configWithCrPat))
	if strings.Contains(string(replaced), "${MY_SECRET}") {
		return
	}
	t.Errorf("replacement unexpected: %s", replaced)
	t.Fail()
}

const configWithCrPat = "services:\n  policy-registry:\n    url: https://ghcr.io\n    type: oci\n    credentials:\n      bearer:\n        token: \"${CR_PAT}\""

const configWithPolCred = "services:\n  policy-registry:\n    url: https://ghcr.io\n    type: oci\n    credentials:\n      bearer:\n        token: \"${OPA_POLICYBUNDLE_PULLCRED}\""
