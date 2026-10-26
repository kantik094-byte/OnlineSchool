from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.authorization import require_content_manager
from app.application.exceptions import CourseNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.module import Module
from app.domain.ordering import check_insert_position, make_room


@dataclass(slots=True)
class CreateModuleCommand:
    course_id: UUID
    title: str
    description: str
    position: int


class CreateModuleUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: CreateModuleCommand) -> Module:
        await require_content_manager(self.idp)

        course = await self.uow.courses.get_for_update(command.course_id)
        if course is None:
            raise CourseNotFoundError("Course not found.")

        siblings = await self.uow.modules.get_by_ids(course.module_ids)
        check_insert_position(siblings, command.position)
        await self.uow.modules.update_many(make_room(siblings, command.position))

        module = Module(
            id=uuid4(),
            course_id=course.id,
            title=command.title,
            description=command.description,
            position=command.position,
        )
        course.add_module(module.id)

        await self.uow.modules.add(module)
        await self.uow.courses.update(course)
        await self.uow.commit()
        return module
