import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from activities import write_to_spicedb, write_to_postgres
from workflows import writeOwner

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233", namespace="default")
    # Run the worker
    worker = Worker(
        client, task_queue="write-task-queue", 
        workflows=[writeOwner], 
        activities=[write_to_spicedb, write_to_postgres]
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())