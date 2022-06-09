package handlers

import (
	ctx "context"

	"github.com/stretchr/testify/mock"
)

//A faked tdf client that meets the interface rules of the real one, to aid in testing
type MockPDPEngine struct {
	mock.Mock
}

func NewMockPDPEngine() PDPEngine {
	pdp := MockPDPEngine{}
	return &pdp
}

func (t *MockPDPEngine) ApplyEntitlementPolicy(
	primaryEntity string,
	secondaryEntities []string,
	idpContextJSON string,
	parentCtx ctx.Context) ([]EntityEntitlement, error) {
	args := t.Called(primaryEntity, secondaryEntities, idpContextJSON, parentCtx)
	return args.Get(0).([]EntityEntitlement), args.Error(1)
}
