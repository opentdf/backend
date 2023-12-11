"""The key master manages the keys."""

import dataclasses
import enum
import logging
from typing import Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)
from cryptography import x509

from tdf3_kas_core.util import get_public_key_from_pem
from tdf3_kas_core.util import get_private_key_from_pem

from tdf3_kas_core.errors import KeyNotFoundError

logger = logging.getLogger(__name__)


class KeyType(enum.Enum):
    PUBLIC = 1
    PRIVATE = 2


@dataclasses.dataclass
class Key:
    name: str


@dataclasses.dataclass
class PrivateKey(Key):
    v_private: PrivateKeyTypes


@dataclasses.dataclass
class PublicKey(Key):
    v_public: PublicKeyTypes | x509.Certificate


class KeyMaster(object):
    """KeyMaster provides keys."""

    def __init__(self):
        """Construct an empty key master.

        Keys is a dictionary containing objects of the form:
            {
                name:     <name string>  # Must be unique
                v_<type>: <key>          # cryptography Key object
            }

        The keys dictionary is indexed by the name strings.
        """
        self.__keys = {}

    def public_key(self, key_name) -> PublicKeyTypes:
        """Get a PUBLIC key object that can be used to encrypt or verify things."""
        if key_name in self.__keys:
            key_obj = self.__keys[key_name]
            if isinstance(key_obj.v_public, x509.Certificate):
                return key_obj.v_public.public_key()
            return key_obj.v_public
        msg = f"Key '{key_name}' not found"
        # This is not necessarily a critical failure,
        # in some cases we fetch the key if it is not cached
        # with key_manager.
        raise KeyNotFoundError(msg)
    
    def get_key(self, key_name) -> PublicKeyTypes | x509.Certificate | PrivateKeyTypes:
        """Get a key object"""
        if key_name in self.__keys:
            key_obj = self.__keys[key_name]
            if isinstance(key_obj, PublicKey):
                return key_obj.v_public
            return key_obj.v_private
        msg = f"Key '{key_name}' not found"
        # This is not necessarily a critical failure,
        # in some cases we fetch the key if it is not cached
        # with key_manager.
        raise KeyNotFoundError(msg)
        

    def private_key(self, key_name) -> PrivateKeyTypes:
        """Get a SECRET key object that can be used to decrypt or sign things."""
        if key_name in self.__keys:
            key_obj = self.__keys[key_name]
            return key_obj.v_private
        msg = f"Key '{key_name}' not found"
        # This is not necessarily a critical failure,
        # in some cases we fetch the key if it is not cached
        # with key_manager.
        raise KeyNotFoundError(msg)

    def get_export_string(self, key_name: str) -> str:
        """Get an exportable key string."""
        if key_name in self.__keys:
            key_obj = self.__keys[key_name]
            if isinstance(key_obj.v_public, x509.Certificate):
                return key_obj.v_public.public_bytes(
                    encoding=serialization.Encoding.PEM
                ).decode("ascii")
            return key_obj.v_public.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii")
        msg = f"Key '{key_name}' not found among {self.__keys}"
        logger.error(msg)
        raise KeyNotFoundError(msg)

    def set_key_pem(self, key_name, key_type, pem_key):
        """Set the pem key directly into the store."""
        if isinstance(key_type, str):
            key_type = KeyType[key_type]
        if key_type == KeyType.PUBLIC:
            key_obj = PublicKey(key_name, get_public_key_from_pem(pem_key))
        else:
            key_obj = PrivateKey(key_name, get_private_key_from_pem(pem_key))
        self.__keys[key_name] = key_obj

    def set_key_path(self, key_name, key_type, key_path):
        """Set the key indirectly by reading a file into the store."""
        if isinstance(key_type, str):
            key_type = KeyType[key_type]
        with open(key_path, "rb") as test_file:
            self.set_key_pem(key_name, key_type, test_file.read())
