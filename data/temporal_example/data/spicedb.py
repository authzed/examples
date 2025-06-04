from authzed.api.v1 import (
        AsyncClient,
        ObjectReference,
        Relationship,
        RelationshipUpdate,
        SubjectReference,
        WriteRelationshipsRequest,
        WriteSchemaRequest,
    )
from grpcutil import insecure_bearer_token_credentials

from shared import BlogAuthor

async def writeRelationship(blog_author: BlogAuthor):
    
    #Using an insecure bearer token for the example. In a real application, you would use a secure bearer token.
    client = AsyncClient(
            "localhost:50051",
            insecure_bearer_token_credentials("localkey"),
        )
    
    try:
        await client.WriteRelationships(
            WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        #It's a temporal best practice to keep activities idempotent
                        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                        relationship=Relationship(
                            resource=ObjectReference(object_type="post", object_id=blog_author.post_id),
                            relation="author",
                            subject=SubjectReference(
                                object=ObjectReference(
                                    object_type="user",
                                    object_id=blog_author.author_user_id,
                                )
                            ),
                        ),
                    ),
                ]
            )
        )
    except Exception as e:
        raise

async def writeSchema():
    SCHEMA = """definition user {}
    definition post {
        relation author: user
        permission edit = author
    }"""
    
    client = AsyncClient(
            "localhost:50051",
            insecure_bearer_token_credentials("localkey"),
        )
    await client.WriteSchema(WriteSchemaRequest(schema=SCHEMA))