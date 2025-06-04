from temporalio import workflow
from datetime import timedelta
from temporalio.exceptions import ActivityError
# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from activities import write_to_postgres
    from activities import write_to_spicedb
    from shared import BlogAuthor
    

#this is the workflow definition
@workflow.defn
class writeOwner:
    @workflow.run
    async def run (self, blog_author: BlogAuthor):
        try:
            workflow.logger.info("Starting workflow execution")

            workflow.logger.info("Attempting Postgres write")
            await workflow.execute_activity(
                write_to_postgres, 
                blog_author, 
                start_to_close_timeout=timedelta(seconds=5),
            )
            workflow.logger.info(f"Postgres write completed")
        except ActivityError as postgresWriteError:
            workflow.logger.error(f"Postgres write failed (from workflow): {postgresWriteError}")
            raise postgresWriteError

        try:
            workflow.logger.info("Attempting SpiceDB write")
            await workflow.execute_activity(
                write_to_spicedb, 
                blog_author, 
                start_to_close_timeout=timedelta(seconds=5),
            )
            workflow.logger.info("SpiceDB write completed")
        except ActivityError as spicedbWriteError:
            workflow.logger.error(f"SpiceDB write failed (from workflow): {spicedbWriteError}")
            raise spicedbWriteError