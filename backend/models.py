from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, async_session
from sqlalchemy.future import select


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
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
