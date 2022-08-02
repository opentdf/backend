"""Access PDP healthz plugin.

We (currently) run the Access PDP as an in-process gRPC server -
it will live and die with KAS itself, but for completeness sake,
this HealthZ plugin will keeping pinging the local gRPC server
to make sure it's still available, and to mark KAS itself as
unhealthy if it is not.
"""

import logging
import grpc


from accesspdp.v1 import accesspdp_pb2_grpc, accesspdp_pb2

from tdf3_kas_core.abstractions import AbstractHealthzPlugin

from tdf3_kas_core.errors import (
    Error,
)

logger = logging.getLogger(__name__)

uri = 'localhost:50052'

class AccessPDPHealthzPlugin(AbstractHealthzPlugin):
    def healthz(self, *, probe):

        logger.info("GRPC STUFF")
        channel = grpc.insecure_channel(uri)
        stub = accesspdp_pb2_grpc.AccessPDPEndpointStub(channel)
        req = accesspdp_pb2.HealthCheckRequest()
        response = stub.Check(req)

        if response.Status == 1:
            logger.debug("--- Ping Access PDP gRPC service successful --- ")
        else:
            logger.debug(f'--- Ping Access PDP gRPC service failed with code {response.Status} --- ')
            raise Error("Unable to be ping Access PDP gRPC service")
