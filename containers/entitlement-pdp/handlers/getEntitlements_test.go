package handlers

import (
	ctx "context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

const entitlementsReq string = `
{
  "primary_entity_id": "74cb12cb-4b53-4c0e-beb6-9ddd8333d6d3",
  "secondary_entity_ids": ["4f6636ca-c60c-40d1-9f3f-015086303f74"],
  "entitlement_context_obj": "{\"subject_attributes\":[{\"http://attribs.com/visibility_level\":\"fuschia\"},{\"http://attribs.com/user_identifier\":\"bupkis@yello.com\"}],\"object_attributes\":[{\"http://attribs.com/min_visibility_level\":\"fuschia\"},{\"http://attribs.com/user_dissem_list\":[\"bupkis@yello.com\",\"nolo@contendere.com\"]}]}"
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

	handler := Entitlements{
		Pdp: testPDP,
	}
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var deserializedResp []EntityEntitlement
	body, err := io.ReadAll(resp.Body)
	assert.Nil(t, err)
	err = json.Unmarshal(body, &deserializedResp)
	assert.Nil(t, err)
	assert.Equal(t, len(deserializedResp), 2)
	assert.Equal(t, deserializedResp[0].EntityId, primaryEntityEntitlement.EntityId)

	testPDP.AssertExpectations(t)
}

func Test_GetEntitlementsHandler_CallsPDP_Error(t *testing.T) {

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

	handler := Entitlements{
		Pdp: testPDP,
	}
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	defer resp.Body.Close()

	assert.Equal(t, http.StatusInternalServerError, resp.StatusCode)

	testPDP.AssertExpectations(t)
}

func Test_GetEntitlementsHandler_RejectsNonPOST(t *testing.T) {

	//Mocked spire GRPC client
	testPDP := new(MockPDPEngine)
	w := httptest.NewRecorder()

	testReq := httptest.NewRequest(http.MethodGet, "http://test", strings.NewReader(entitlementsReq))

	handler := Entitlements{
		Pdp: testPDP,
	}
	handler.ServeHTTP(w, testReq)

	resp := w.Result()
	defer resp.Body.Close()

	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)

	testPDP.AssertExpectations(t)
}

// from https://cs.opensource.google/go/go/+/master:src/errors/join_test.go

func TestJoinReturnsNil(t *testing.T) {
	if err := ErrJoin(); err != nil {
		t.Errorf("errors.Join() = %v, want nil", err)
	}
	if err := ErrJoin(nil); err != nil {
		t.Errorf("errors.Join(nil) = %v, want nil", err)
	}
	if err := ErrJoin(nil, nil); err != nil {
		t.Errorf("errors.Join(nil, nil) = %v, want nil", err)
	}
}

func TestJoin(t *testing.T) {
	err1 := errors.New("err1")
	err2 := errors.New("err2")
	for _, test := range []struct {
		errs []error
		want []error
	}{{
		errs: []error{err1},
		want: []error{err1},
	}, {
		errs: []error{err1, err2},
		want: []error{err1, err2},
	}, {
		errs: []error{err1, nil, err2},
		want: []error{err1, err2},
	}} {
		got := ErrJoin(test.errs...).(interface{ Unwrap() []error }).Unwrap()
		if !reflect.DeepEqual(got, test.want) {
			t.Errorf("Join(%v) = %v; want %v", test.errs, got, test.want)
		}
		if len(got) != cap(got) {
			t.Errorf("Join(%v) returns errors with len=%v, cap=%v; want len==cap", test.errs, len(got), cap(got))
		}
	}
}

func TestJoinErrorMethod(t *testing.T) {
	err1 := errors.New("err1")
	err2 := errors.New("err2")
	for _, test := range []struct {
		errs []error
		want string
	}{{
		errs: []error{err1},
		want: "err1",
	}, {
		errs: []error{err1, err2},
		want: "err1\nerr2",
	}, {
		errs: []error{err1, nil, err2},
		want: "err1\nerr2",
	}} {
		got := ErrJoin(test.errs...).Error()
		if got != test.want {
			t.Errorf("Join(%v).Error() = %q; want %q", test.errs, got, test.want)
		}
	}
}

type MockPDPEngine struct {
	mock.Mock
}

func (t *MockPDPEngine) ApplyEntitlementPolicy(
	primaryEntity string,
	secondaryEntities []string,
	entitlementContextJSON string,
	parentCtx ctx.Context) ([]EntityEntitlement, error) {
	args := t.Called(primaryEntity, secondaryEntities, entitlementContextJSON, parentCtx)
	return args.Get(0).([]EntityEntitlement), args.Error(1)
}
