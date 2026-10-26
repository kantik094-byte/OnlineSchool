from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repositories.section_repository import SectionRepository
from app.domain.entities.section import Section
from app.infrastructure.database.mappers.section_mapper import SectionMapper
from app.infrastructure.database.models.section_model import SectionModel


class SqlAlchemySectionRepository(SectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, section_id: UUID) -> Section | None:
        stmt = (
            select(SectionModel)
            .options(selectinload(SectionModel.lectures))
            .where(SectionModel.id == str(section_id))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return None if model is None else SectionMapper.to_domain(model)

    async def get_by_ids(self, section_ids: list[UUID]) -> list[Section]:
        if not section_ids:
            return []

        stmt = (
            select(SectionModel)
            .options(selectinload(SectionModel.lectures))
            .where(SectionModel.id.in_([str(item) for item in section_ids])).execution_options(populate_existing=True)
        )

        result = await self.session.execute(stmt)
        return [SectionMapper.to_domain(model) for model in result.scalars().all()]

    async def get_for_update(self, section_id: UUID) -> Section | None:
        stmt = (select(SectionModel).
                options(selectinload(SectionModel.lectures)).
                where(SectionModel.id == str(section_id)).
                with_for_update().
                execution_options(populate_existing=True)
        )

        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return None if model is None else SectionMapper.to_domain(model)

    async def add(self, section: Section) -> None:
        self.session.add(SectionMapper.to_model(section))
        await self.session.flush()

    async def update(self, section: Section) -> None:
        model = await self.session.get(SectionModel, str(section.id))
        if model is None:
            return
        model.title = section.title
        model.description = section.description
        model.position = section.position
        await self.session.flush()

    async def update_many(self, sections: list[Section]) -> None:
        if not sections:
            return

        await self.session.execute(
            update(SectionModel),
            [
                {"id": str(section.id), "title": section.title, "description": section.description, "position": section.position} for section in sections
            ]
        )
        await self.session.flush()

    async def remove(self, section: Section) -> None:
        await self.session.execute(delete(SectionModel).where(SectionModel.id == str(section.id)))
        await self.session.flush()