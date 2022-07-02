package handlers

import (
	"encoding/json"
	"io"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"
)

const token_resp string = `
{ 
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "token_type": "Bearer",
  "expires_in": 3600,
}`

const by_email_bob_resp = `[
{"id": "bobid", "username":"bob.smith"}
]
`
const by_email_alice_resp = `[
{"id": "aliceid", "username":"alice.smith"}
]
`
const by_username_bob_resp = `[
{"id": "bobid", "username":"bob.smith"}
]`

func test_keycloakConfig(server *httptest.Server) KeyCloakConfg {
	return KeyCloakConfg{
		Url:          server.URL,
		ClientId:     "c1",
		ClientSecret: "cs",
		Realm:        "tdf",
		AuthPath:     false,
	}
}
func test_server(t *testing.T, userSearchQueryAndResp map[string]string) *httptest.Server {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/realms/tdf/protocol/openid-connect/token" {
			_, err := io.WriteString(w, token_resp)
			if err != nil {
				t.Error(err)
			}
		} else if r.URL.Path == "/admin/realms/tdf/users" {
			i, ok := userSearchQueryAndResp[r.URL.RawQuery]
			if ok == true {
				w.Header().Set("Content-Type", "application/json")
				_, err := io.WriteString(w, i)
				if err != nil {
					t.Error(err)
				}
			} else {
				t.Errorf("UnExpected Request, got: %s", r.URL.Path)
			}
		} else {
			t.Errorf("UnExpected Request, got: %s", r.URL.Path)
		}
	}))
	return server
}

func Test_BadRequest_Get(t *testing.T) {

	zapLog, _ := zap.NewDevelopment()

	server := test_server(t, map[string]string{})
	defer server.Close()

	testReq := httptest.NewRequest(http.MethodGet, "http://test",
		strings.NewReader(`{"type": "email","identifiers": ["bob@sample.org"]}`))
	handler := GetEntityResolutionHandler(test_keycloakConfig(server), zapLog.Sugar())
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)
}

func Test_BadRequestPost(t *testing.T) {

	zapLog, _ := zap.NewDevelopment()

	server := test_server(t, map[string]string{})
	defer server.Close()

	// invalid type
	testReq := httptest.NewRequest(http.MethodPost, "http://test",
		strings.NewReader(`{"type": "somebadtype","identifiers": ["bob@sample.org"]}`))
	handler := GetEntityResolutionHandler(test_keycloakConfig(server), zapLog.Sugar())
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)

	// no type
	testReq2 := httptest.NewRequest(http.MethodPost, "http://test",
		strings.NewReader(`{"identifiers": ["bob@sample.org"]}`))
	handler2 := GetEntityResolutionHandler(test_keycloakConfig(server), zapLog.Sugar())
	w2 := httptest.NewRecorder()
	handler2.ServeHTTP(w2, testReq2)

	resp2 := w2.Result()
	assert.Equal(t, http.StatusBadRequest, resp2.StatusCode)
}

func Test_ByEmail(t *testing.T) {
	zapLog, _ := zap.NewDevelopment()

	server := test_server(t, map[string]string{
		"email=bob%40sample.org":   by_email_bob_resp,
		"email=alice%40sample.org": by_email_alice_resp,
	})
	defer server.Close()

	testReq := httptest.NewRequest(http.MethodPost, "http://test",
		strings.NewReader(`{"type": "email","identifiers": ["bob@sample.org","alice@sample.org"]}`))
	handler := GetEntityResolutionHandler(test_keycloakConfig(server), zapLog.Sugar())
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var deserializedResp EntityResolutionResponse
	body, err := ioutil.ReadAll(resp.Body)
	assert.Nil(t, err)
	err = json.Unmarshal(body, &deserializedResp)
	assert.Nil(t, err)
	assert.Equal(t, 2, len(deserializedResp.EntityResolutions))
	assert.Equal(t, "bob@sample.org", deserializedResp.EntityResolutions[0].Identifier)
	assert.Equal(t, 1, len(deserializedResp.EntityResolutions[0].EntityIdentifiers))
	assert.Equal(t, "bobid", deserializedResp.EntityResolutions[0].EntityIdentifiers[0])
	assert.Equal(t, "alice@sample.org", deserializedResp.EntityResolutions[1].Identifier)
	assert.Equal(t, 1, len(deserializedResp.EntityResolutions[1].EntityIdentifiers))
	assert.Equal(t, "aliceid", deserializedResp.EntityResolutions[1].EntityIdentifiers[0])
}

func Test_ByUsername(t *testing.T) {
	zapLog, _ := zap.NewDevelopment()

	server := test_server(t, map[string]string{
		"username=bob.smith": by_username_bob_resp,
	})
	defer server.Close()

	testReq := httptest.NewRequest(http.MethodPost, "http://test", strings.NewReader(`{"type": "username","identifiers": ["bob.smith"]}`))
	handler := GetEntityResolutionHandler(test_keycloakConfig(server), zapLog.Sugar())
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var deserializedResp EntityResolutionResponse
	body, err := ioutil.ReadAll(resp.Body)
	assert.Nil(t, err)
	err = json.Unmarshal(body, &deserializedResp)
	assert.Nil(t, err)
	assert.Equal(t, 1, len(deserializedResp.EntityResolutions))
	assert.Equal(t, "bob.smith", deserializedResp.EntityResolutions[0].Identifier)
	assert.Equal(t, 1, len(deserializedResp.EntityResolutions[0].EntityIdentifiers))
	assert.Equal(t, "bobid", deserializedResp.EntityResolutions[0].EntityIdentifiers[0])
}
