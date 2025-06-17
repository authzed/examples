# NOTE: This is a simple example of how to use retries. There are certain things like TLS, etc. that are not included here for brevity.

from authzed.api.v1 import (
    Client,
    ObjectReference,
    Relationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
)
from grpcutil import insecure_bearer_token_credentials
import json


service_config_json = json.dumps(
    {
        "methodConfig": [
            {
                #NOTE: This retry will only apply to the WriteRelationships method, to apply retry to all methods, put [{}] in the "name" field
                "name": [{"service": "authzed.api.v1.PermissionsService", "method": "WriteRelationships"}],
                "retryPolicy": {
                    "maxAttempts": 3,
                    "initialBackoff": "1s",
                    "maxBackoff": "4s",
                    "backoffMultiplier": 2.0,
                    "retryableStatusCodes": ['UNAVAILABLE', 'RESOURCE_EXHAUSTED', 'DEADLINE_EXCEEDED', 'ABORTED'],
                },
            }
        ]
    }
)
options = []
options.append(("grpc.service_config", service_config_json))
 
 # NOTE: it's also recommended to implement a retry policy for the client connection, however that is omitted here for brevity
client = Client(
    "localhost:50051",
    insecure_bearer_token_credentials("abc123"),
    options=options,
)
 
resp = client.WriteRelationships(
    WriteRelationshipsRequest(
        updates=[
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id="1"),
                    relation="owner",
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type="user",
                            object_id="tom",
                        )
                    ),
                ),
            ),
        ]
    )
)
 
print(resp.written_at.token)