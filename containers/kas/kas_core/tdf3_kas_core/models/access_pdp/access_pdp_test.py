import unittest
from unittest.mock import patch, Mock
import grpc
from tdf3_kas_core.errors import AuthorizationError
from tdf3_kas_core.models.access_pdp import AccessPDP


class TestAccessPDP(unittest.TestCase):
    @patch('grpc.insecure_channel')  # Replace 'your_module' with the actual module name
    @patch('accesspdp.v1.accesspdp_pb2_grpc.AccessPDPEndpointStub')
    def test_check_attributes_grpc_error(self, MockStub, _):
        # Given an AccessPDP instance
        pdp = AccessPDP()

        # And a mock gRPC stub that raises an RpcError when DetermineAccess is called
        mock_stub_instance = Mock()
        mock_stub_instance.DetermineAccess.side_effect = grpc.RpcError("Some gRPC error")
        MockStub.return_value = mock_stub_instance

        # When _check_attributes is called
        with self.assertRaises(AuthorizationError) as context:
            pdp._check_attributes({}, {}, {})

        # Then an AuthorizationError should be raised with the error message from the RpcError
        self.assertEqual(str(context.exception), "Some gRPC error")


if __name__ == "__main__":
    unittest.main()
