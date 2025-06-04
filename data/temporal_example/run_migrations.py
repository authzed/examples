from data.postgres import create_blog_authors_table
from data.spicedb import writeSchema
import asyncio

async def main():
    await create_blog_authors_table()
    await writeSchema()

if __name__ == "__main__":
    asyncio.run(main())