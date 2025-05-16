from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, async_session
from sqlalchemy.future import select


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
    content_generated = Column(String, default="false")
    sections = relationship("Section", back_populates="document")

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    section_name = Column(String, nullable=False)
    content = Column(Text, default="")
    feedback = Column(Text, default="")
    status = Column(String, default="pending")  # pending | completed | needs_review

    document = relationship("Document", back_populates="sections")


async def save_section_to_db_async(document_id: str, section_name: str, content_html: str):
    async with async_session() as session:
        new_section = Section(
            document_id=document_id,
            section_name=section_name,
            content=content_html,
            status="completed"
        )
        session.add(new_section)
        await session.commit()
        await session.refresh(new_section)
        return str(new_section.id)

def save_section_to_db(document_id: str, section_name: str, content_html: str):
    """Synchronous wrapper for the async function"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            result = new_loop.run_until_complete(save_section_to_db_async(document_id, section_name, content_html))
            new_loop.close()
            return result
        else:
            return loop.run_until_complete(save_section_to_db_async(document_id, section_name, content_html))
    except Exception as e:
        print(f"Error in save_section_to_db: {str(e)}")
        return str(hash(f"{document_id}-{section_name}-{hash(content_html)}"))

async def get_next_section(document_id: int):
    async with async_session() as session:
        stmt = select(Section).where(
            Section.document_id == document_id,
            Section.status == "pending"
        ).order_by(Section.id.asc())
        result = await session.execute(stmt)
        return result.scalars().first()


async def is_document_content_generated_async(document_id: str):
    """Check if a document has already had content generated"""
    try:
        async with async_session() as session:
            try:
                # Convert string document_id to integer
                doc_id_int = int(document_id)
                
                # First try with ORM
                try:
                    stmt = select(Document).where(Document.id == doc_id_int)
                    result = await session.execute(stmt)
                    document = result.scalar_one_or_none()
                    # Safely check if content_generated attribute exists and is true
                    if document and hasattr(document, 'content_generated') and document.content_generated == "true":
                        return True
                except Exception as orm_error:
                    # If ORM fails (likely due to column not existing), try with raw SQL
                    print(f"ORM query failed, trying raw SQL: {str(orm_error)}")
                    await session.rollback()  # Roll back the failed transaction
                    
                    # Use raw SQL to check if document exists at all
                    from sqlalchemy import text
                    result = await session.execute(
                        text("SELECT id FROM documents WHERE id = :id"),
                        {"id": doc_id_int}
                    )
                    if result.scalar_one_or_none():
                        # Document exists but likely without content_generated column
                        return False
                
                return False
            except ValueError:
                # Handle case where document_id is not a valid integer
                print(f"Invalid document ID format: {document_id}")
                return False
    except Exception as e:
        print(f"Error checking if document content generated: {str(e)}")
        return False

def is_document_content_generated(document_id: str):
    """Synchronous wrapper to check if document content is generated"""
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            result = new_loop.run_until_complete(is_document_content_generated_async(document_id))
            new_loop.close()
            return result
        else:
            return loop.run_until_complete(is_document_content_generated_async(document_id))
    except Exception as e:
        print(f"Error in is_document_content_generated: {str(e)}")
        return False

async def update_section_feedback_async(section_id: str, feedback_type: str, edited_content: str = None):
    async with async_session() as session:
        stmt = select(Section).where(Section.id == section_id)
        result = await session.execute(stmt)
        section = result.scalar_one_or_none()
        if section:
            if edited_content:
                section.content = edited_content
            
            section.feedback = feedback_type
            
            section.status = "pending" if feedback_type == "regenerate" else "completed"
            await session.commit()

def update_section_feedback(section_id: str, feedback_type: str, edited_content: str = None):
    """Synchronous wrapper for the async function"""
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_section_feedback_async(section_id, feedback_type, edited_content))


async def mark_document_content_generated_async(document_id: str):
    """Mark a document as having generated content"""
    try:
        # Ensure we're using the correct event loop
        loop = asyncio.get_running_loop()
        
        async with async_session() as session:
            # First try with the ORM approach
            try:
                stmt = select(Document).where(Document.id == document_id)
                result = await session.execute(stmt)
                document = result.scalar_one_or_none()
                if document:
                    document.content_generated = "true"
                    await session.commit()
            except Exception as orm_error:
                # If that fails (likely due to missing column), try with raw SQL
                print(f"ORM update failed, trying raw SQL: {str(orm_error)}")
                await session.rollback()
                
                # Check if the column exists first
                from sqlalchemy import text
                try:
                    # Try to add the column if it doesn't exist
                    await session.execute(text(
                        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_generated VARCHAR DEFAULT 'false'"
                    ))
                    
                    # Now update the record
                    await session.execute(
                        text("UPDATE documents SET content_generated = 'true' WHERE id = :id"),
                        {"id": document_id}
                    )
                    await session.commit()
                    print(f"Added content_generated column and updated document {document_id}")
                except Exception as sql_error:
                    await session.rollback()
                    print(f"Failed to add column or update document: {str(sql_error)}")
    except RuntimeError as re:
        print(f"Async loop issue in mark_document_content_generated_async: {str(re)}")
        # Handle case where we don't have an event loop running
        # This is a simpler fallback approach
        from sqlalchemy import text
        async with async_session() as session:
            try:
                await session.execute(
                    text("UPDATE documents SET content_generated = 'true' WHERE id = :id"),
                    {"id": document_id}
                )
                await session.commit()
                print(f"Updated document {document_id} content_generated status with fallback method")
            except Exception as fallback_error:
                await session.rollback()
                print(f"Fallback update failed: {str(fallback_error)}")
    except Exception as e:
        print(f"Error in mark_document_content_generated_async: {str(e)}")

def mark_document_content_generated(document_id: str):
    """Synchronous wrapper to mark document content as generated"""
    try:
        import asyncio
        
        # Create a separate, isolated loop to avoid loop attachment issues
        new_loop = asyncio.new_event_loop()
        try:
            new_loop.run_until_complete(mark_document_content_generated_async(document_id))
        except Exception as loop_error:
            print(f"Error running mark_document_content_generated_async: {str(loop_error)}")
        finally:
            new_loop.close()
            
    except Exception as e:
        print(f"Error in mark_document_content_generated: {str(e)}")
        # Fallback to direct database update if possible
        try:
            from sqlalchemy import create_engine, text
            from database import SQLALCHEMY_DATABASE_URL
            engine = create_engine(SQLALCHEMY_DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("UPDATE documents SET content_generated = 'true' WHERE id = :id"),
                             {"id": document_id})
                conn.commit()
                print(f"Updated document {document_id} using synchronous fallback")
        except Exception as db_error:
            print(f"Synchronous fallback failed: {str(db_error)}")
