from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import LectureNotFoundError, SectionNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.ordering import close_gap


@dataclass(slots=True)
class DeleteLectureCommand:
    lecture_id: UUID



class DeleteLectureUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: DeleteLectureCommand) -> None:
        await require_content_manager(self.idp)

        lecture = await self.uow.lectures.get_by_id(command.lecture_id)
        if not lecture:
            raise LectureNotFoundError("Lecture not found")

        section = await self.uow.sections.get_for_update(lecture.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        siblings = await self.uow.lectures.get_by_ids(section.lecture_ids)
        lecture = next((item for item in siblings if item.id == command.lecture_id), None)
        if lecture is None:
            raise LectureNotFoundError('Lecture not found.')

        section.remove_lecture(command.lecture_id)
        await self.uow.lectures.remove(lecture)
        await self.uow.sections.update(section)
        await self.uow.lectures.update_many(close_gap(siblings, lecture.position))

        await self.uow.commit()


