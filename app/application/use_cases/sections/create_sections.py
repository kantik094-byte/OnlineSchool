from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.authorization import require_content_manager
from app.application.exceptions import CourseModuleNotFoundError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.section import Section
from app.domain.ordering import check_insert_position, make_room


@dataclass(slots=True)
class CreateSectionCommand:
    module_id: UUID
    title: str
    description: str
    position: int


class CreateSectionUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: CreateSectionCommand) -> Section:
        await require_content_manager(self.idp)

        module = await self.uow.modules.get_for_update(command.module_id)
        if module is None:
            raise CourseModuleNotFoundError('Module not found.')

        siblings = await self.uow.sections.get_by_ids(module.section_ids)
        check_insert_position(siblings, command.position)
        await self.uow.sections.update_many(make_room(siblings, command.position))

        section = Section(
            id=uuid4(),
            module_id=command.module_id,
            title=command.title,
            description=command.description,
            position=command.position,
        )
        module.add_section(section.id)
        await self.uow.sections.add(section)
        await self.uow.modules.update(module)
        await self.uow.commit()
        return section
