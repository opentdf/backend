package handlers

import (
	"encoding/json"
	"errors"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"go.uber.org/zap"
)

const entitlementsReq string = `
{
  "primary_entity_id": "74cb12cb-4b53-4c0e-beb6-9ddd8333d6d3",
  "secondary_entity_ids": ["4f6636ca-c60c-40d1-9f3f-015086303f74"],
  "idp_context_obj": "{\"subject_attributes\":[{\"http://attribs.com/visibility_level\":\"fuschia\"},{\"http://attribs.com/user_identifier\":\"bupkis@yello.com\"}],\"object_attributes\":[{\"http://attribs.com/min_visibility_level\":\"fuschia\"},{\"http://attribs.com/user_dissem_list\":[\"bupkis@yello.com\",\"nolo@contendere.com\"]}]}"
}
`

var primaryEntityEntitlement EntityEntitlement = EntityEntitlement{
	EntityId: "74cb12cb-4b53-4c0e-beb6-9ddd8333d6d3",
	EntityAttributes: []EntityAttribute{
		{
			Attribute:   "https://example.com/attr/Classification/value/S",
			DisplayName: "Classification",
		},
		{
			Attribute:   "https://example.com/attr/COI/value/PRX",
			DisplayName: "COI",
		},
	},
}

var secondaryEntityEntitlement1 EntityEntitlement = EntityEntitlement{
	EntityId: "4f6636ca-c60c-40d1-9f3f-015086303f74",
	EntityAttributes: []EntityAttribute{
		{
			Attribute:   "https://example.org/attr/OPA/value/AddedByOPA",
			DisplayName: "Added By OPA",
		},
	},
}

func Test_GetEntitlementsHandler_CallsPDP_Success(t *testing.T) {
	zapLog, _ := zap.NewDevelopment()

	primaryUID := "74cb12cb-4b53-4c0e-beb6-9ddd8333d6d3"
	secondaryUIDs := []string{"4f6636ca-c60c-40d1-9f3f-015086303f74"}
	//Mocked spire GRPC client
	testPDP := new(MockPDPEngine)
	testPDP.On("ApplyEntitlementPolicy", primaryUID, secondaryUIDs, mock.Anything, mock.Anything).Return(
		[]EntityEntitlement{primaryEntityEntitlement, secondaryEntityEntitlement1},
		nil,
	)

	w := httptest.NewRecorder()
	testReq := httptest.NewRequest(http.MethodPost, "http://test", strings.NewReader(entitlementsReq))

	handler := GetEntitlementsHandler(testPDP, zapLog.Sugar())
	handler.ServeHTTP(w, testReq)

	resp := w.Result()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var deserializedResp []EntityEntitlement
	body, err := ioutil.ReadAll(resp.Body)
	assert.Nil(t, err)
	err = json.Unmarshal(body, &deserializedResp)
	assert.Nil(t, err)
	assert.Equal(t, len(deserializedResp), 2)
	assert.Equal(t, deserializedResp[0].EntityId, primaryEntityEntitlement.EntityId)

	testPDP.AssertExpectations(t)
}

func Test_GetEntitlementsHandler_CallsPDP_Error(t *testing.T) {
	zapLog, _ := zap.NewDevelopment()

	primaryUID := "74cb12cb-4b53-4c0e-beb6-9ddd8333d6d3"
	secondaryUIDs := []string{"4f6636ca-c60c-40d1-9f3f-015086303f74"}
	//Mocked spire GRPC client
	testPDP := new(MockPDPEngine)
	testPDP.On("ApplyEntitlementPolicy", primaryUID, secondaryUIDs, mock.Anything, mock.Anything).Return(
		[]EntityEntitlement{},
		errors.New("I POOPED THE BED"),
	)

	w := httptest.NewRecorder()
	testReq := httptest.NewRequest(http.MethodPost, "http://test", strings.NewReader(entitlementsReq))

	handler := GetEntitlementsHandler(testPDP, zapLog.Sugar())
	handler.ServeHTTP(w, testReq)

	resp := w.Result()

	assert.Equal(t, http.StatusInternalServerError, resp.StatusCode)

	testPDP.AssertExpectations(t)
}

func Test_GetEntitlementsHandler_RejectsNonPOST(t *testing.T) {
	zapLog, _ := zap.NewDevelopment()

	//Mocked spire GRPC client
	testPDP := new(MockPDPEngine)
	w := httptest.NewRecorder()

	testReq := httptest.NewRequest(http.MethodGet, "http://test", strings.NewReader(entitlementsReq))

	handler := GetEntitlementsHandler(testPDP, zapLog.Sugar())
	handler.ServeHTTP(w, testReq)

	resp := w.Result()

	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)

	testPDP.AssertExpectations(t)
}
