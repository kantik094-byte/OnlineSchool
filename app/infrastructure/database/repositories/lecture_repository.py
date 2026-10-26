from uuid import UUID

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories.lecture_repository import LectureRepository
from app.domain.entities.lecture import Lecture
from app.infrastructure.database.mappers.lecture_mapper import LectureMapper
from app.infrastructure.database.models.lecture_model import LectureModel


class SqlAlchemyLectureRepository(LectureRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, lecture_id: UUID) -> Lecture | None:
        model = await self.session.get(LectureModel, str(lecture_id))
        return None if model is None else LectureMapper.to_domain(model)

    async def get_by_ids(self, lecture_ids: list[UUID]) -> list[Lecture]:
        if not lecture_ids:
            return []
        stmt = select(LectureModel).where(
            LectureModel.id.in_([str(item) for item in lecture_ids]).execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return [LectureMapper.to_domain(model) for model in result.scalars().all()]

    async def get_for_update(self, lecture_id: UUID) -> Lecture | None:
        stmt = select(LectureModel).where(LectureModel.id == str(lecture_id)).with_for_update().execution_options(populate_existing=True)
        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return None if model is None else LectureMapper.to_domain(model)


    async def add(self, lecture: Lecture) -> None:
        self.session.add(LectureMapper.to_model(lecture))
        await self.session.flush()

    async def update(self, lecture: Lecture) -> None:
        model = await self.session.get(LectureModel, str(lecture.id))
        if model is None:
            return
        model.title = lecture.title
        model.content = lecture.content
        model.position = lecture.position
        await self.session.flush()

    async def update_many(self, lectures: list[Lecture]) -> None:
        if not lectures:
            return

        await self.session.execute(
            update(LectureModel),
            [
                {'id': str(lecture.id), 'title': lecture.title, 'content': lecture.content, 'position': lecture.position} for lecture in lectures
            ],
        )

        await self.session.flush()

    async def remove(self, lecture: Lecture) -> None:
        await self.session.execute(delete(LectureModel).where(LectureModel.id == str(lecture.id)))
        await self.session.flush()