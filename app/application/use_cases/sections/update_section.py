from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import SectionNotFoundError
from app.application.authorization import require_content_manager
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.section import Section


@dataclass(slots=True)
class UpdateSectionCommand:
    section_id: UUID
    title: str
    description: str
    position: int


class UpdateSectionUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: UpdateSectionCommand) -> Section:
        await require_content_manager(self.idp)

        async with self.uow:
            section = await self.uow.sections.get_by_id(command.section_id)
            if section is None:
                raise SectionNotFoundError("Section not found.")

            section.update(
                title=command.title,
                description=command.description,
                position=command.position,
            )
            await self.uow.sections.update(section)

            await self.uow.commit()
            return section