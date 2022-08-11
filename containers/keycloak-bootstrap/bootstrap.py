#!/usr/bin/env python3

import logging
from keycloak_bootstrap import kc_bootstrap
from entitlements_bootstrap import entitlements_bootstrap
from attributes_bootstrap import attributes_bootstrap

logging.basicConfig()
logger = logging.getLogger("keycloak_bootstrap")
logger.setLevel(logging.DEBUG)


def main():
    kc_bootstrap()
    attributes_bootstrap()
    entitlements_bootstrap()


if __name__ == "__main__":
    main()
