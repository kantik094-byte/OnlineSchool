from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import CourseModuleNotFoundError, CourseNotFoundError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities.module import Module
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateModuleCommand:
    module_id: UUID
    title: str
    description: str
    position: int


class UpdateModuleUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: UpdateModuleCommand) -> Module:
        module = await self.access.ensure_can_manage_module(command.module_id)

        course = await self.uow.courses.get_for_update(module.course_id)
        if course is None:
            raise CourseNotFoundError('Course not found.')

        siblings = await self.uow.modules.get_by_ids(course.module_ids)

        module = next((item for item in siblings if item.id == command.module_id), None)
        if module is None:
            raise CourseModuleNotFoundError('Module not found.')

        siblings = [item for item in siblings if item.id != module.id]
        check_insert_position(siblings, command.position)
        old_position = module.position

        module.update(
            title=command.title,
            description=command.description,
            position=command.position,
        )

        await self.uow.modules.update_many(move_position(siblings, old_position, command.position))
        await self.uow.modules.update(module)
        await self.uow.commit()

        return module
