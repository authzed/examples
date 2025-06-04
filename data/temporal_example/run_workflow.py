import asyncio
import argparse

from run_worker import writeOwner
from temporalio.client import Client
from shared import BlogAuthor

#In a real application, you may invoke this code when someone submits a form, presses a button, or visits a certain URL

async def main(author_user_id: str, post_id: str):
    client = await Client.connect("localhost:7233")

    await client.execute_workflow(
        writeOwner.run, BlogAuthor(author_user_id=author_user_id, post_id=post_id), id=f"write-workflow-{author_user_id}-{post_id}", task_queue="write-task-queue"
    )

    print("Workflow completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the workflow with specified author and post IDs')
    parser.add_argument('--author', required=True, help='The author user ID')
    parser.add_argument('--post', required=True, help='The post ID')
    
    args = parser.parse_args()
    asyncio.run(main(args.author, args.post))