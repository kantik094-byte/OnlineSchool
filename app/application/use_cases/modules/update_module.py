from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import ModuleNotFoundError
from app.application.authorization import require_content_manager
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.module import Module


@dataclass(slots=True)
class UpdateModuleCommand:
    module_id: UUID
    title: str
    description: str
    position: int


class UpdateModuleUseCase:
    def __init__(self, uow: UnitOfWork, idp: IdentityProvider) -> None:
        self.uow = uow
        self.idp = idp

    async def execute(self, command: UpdateModuleCommand) -> Module:
        await require_content_manager(self.idp)

        async with self.uow:
            module = await self.uow.modules.get_by_id(command.module_id)
            if module is None:
                raise ModuleNotFoundError('Module not found.')

            module.update(
                title=command.title,
                description=command.description,
                position=command.position,
            )
            await self.uow.modules.update(module)
            await self.uow.commit()
            return module