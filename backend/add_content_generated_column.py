from sqlalchemy import text
from database import engine
import asyncio

async def add_content_generated_column():
    """Add the content_generated column to the documents table if it doesn't exist"""
    async with engine.begin() as conn:
        # Check if column exists
        check_column_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'content_generated'
        """)
        result = await conn.execute(check_column_query)
        column_exists = result.fetchone() is not None

        if not column_exists:
            print("Adding content_generated column to documents table...")
            # Add the column
            await conn.execute(
                text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_generated VARCHAR DEFAULT 'false'")
            )
            print("Column added successfully!")
        else:
            print("content_generated column already exists")

if __name__ == "__main__":
    asyncio.run(add_content_generated_column())
