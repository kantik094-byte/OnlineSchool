from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.authorization import require_content_manager
from app.application.exceptions import SectionNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.lecture import Lecture
from app.domain.ordering import make_room, check_insert_position


@dataclass(slots=True)
class CreateLectureCommand:
    section_id: UUID
    title: str
    content: str
    position: int


class CreateLectureUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: CreateLectureCommand) -> Lecture:
        await require_content_manager(self.idp)

        section = await self.uow.sections.get_for_update(command.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        siblings = await self.uow.lectures.get_by_ids(section.lecture_ids)
        check_insert_position(siblings, command.position)
        await self.uow.lectures.update_many(make_room(siblings, command.position))

        lecture = Lecture(
            id=uuid4(),
            section_id=command.section_id,
            title=command.title,
            content=command.content,
            position=command.position,
        )

        section.add_lecture(lecture.id)
        await self.uow.lectures.add(lecture)
        await self.uow.sections.update(section)
        await self.uow.commit()
        return lecture
