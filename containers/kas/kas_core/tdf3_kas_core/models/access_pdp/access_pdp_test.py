import unittest
from unittest.mock import patch, Mock
from tdf3_kas_core.models.access_pdp import AccessPDP


class TestAccessPDP(unittest.TestCase):
    def setUp(self):
        self.access_pdp = AccessPDP()

    @patch('tdf3_kas_core.models.pdp_grpc.convert_attribute_defs', return_value=None)
    def test_check_attributes_with_none_attr_defs(self, _):
        data_attributes = Mock()
        entity_attributes = Mock()
        data_attribute_definitions = Mock()

        with self.assertRaises(AuthorizationError) as context:
            self.access_pdp._check_attributes(data_attributes, entity_attributes, data_attribute_definitions)

        self.assertEqual(str(context.exception), "Invalid Attribute")


if __name__ == '__main__':
    unittest.main()
