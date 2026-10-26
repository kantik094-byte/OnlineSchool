from dataclasses import dataclass
from uuid import UUID

from app.application.authorization import require_content_manager
from app.application.exceptions import LectureNotFoundError, SectionNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.lecture import Lecture
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateLectureCommand:
    lecture_id: UUID
    title: str
    content: str
    position: int


class UpdateLectureUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: UpdateLectureCommand) -> Lecture:
        await require_content_manager(self.idp)

        lecture = await self.uow.lectures.get_by_id(command.lecture_id)
        if lecture is None:
            raise LectureNotFoundError("Lecture not found.")

        section = await self.uow.sections.get_for_update(lecture.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        siblings = await self.uow.lectures.get_by_ids(section.lecture_ids)

        lecture = next((item for item in siblings if item.id == command.lecture_id), None)
        if lecture is None:
            raise LectureNotFoundError('Lecture not found.')

        siblings = [item for item in siblings if item.id != lecture.id]
        check_insert_position(siblings, command.position)
        old_position = lecture.position

        lecture.update(
            title=command.title,
            content=command.content,
            position=command.position,
        )

        await self.uow.lectures.update_many(move_position(siblings, old_position, command.position))
        await self.uow.lectures.update(lecture)
        await self.uow.commit()

        return lecture
