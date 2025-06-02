import psycopg

from shared import BlogAuthor

DB_CONFIG = {
    "dbname": "blog_authors",
    "user": "dev",
    "password": "abc123",
    "host": "localhost",
    "port": 5432
}

async def writePostgres(blog_author: BlogAuthor):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO blog_authors (author_user_id, post_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (blog_author.author_user_id, blog_author.post_id))

async def create_blog_authors_table():
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blog_authors (
                    author_user_id TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    PRIMARY KEY (author_user_id, post_id)
                );
            """)