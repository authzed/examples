from temporalio import activity
from shared import BlogAuthor
from data.spicedb import writeRelationship
from data.postgres import writePostgres
import psycopg


@activity.defn
async def write_to_spicedb(blog_author: BlogAuthor):
    try:
        await writeRelationship(blog_author)
    except Exception:
        activity.logger.exception("SpiceDB write failed")
        raise

@activity.defn
async def write_to_postgres(blog_author: BlogAuthor):
    try:
        await writePostgres(blog_author)
    except Exception:
        activity.logger.exception("Postgres write failed")
        raise
