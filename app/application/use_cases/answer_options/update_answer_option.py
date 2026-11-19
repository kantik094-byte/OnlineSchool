from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import AnswerOptionNotFoundError, QuestionNotFoundError, QuestionAlreadyUsedError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities.answer_option import AnswerOption
from app.domain.ordering import check_insert_position, move_position


@dataclass(slots=True)
class UpdateAnswerOptionCommand:
    answer_option_id: UUID
    text: str
    position: int
    is_correct: bool


class UpdateAnswerOptionUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access


    async def execute(self, command: UpdateAnswerOptionCommand) -> AnswerOption:
        answer_option = await self.uow.answer_options.get_by_id(command.answer_option_id)
        if answer_option is None:
            raise AnswerOptionNotFoundError('Answer option not found.')

        await self.access.ensure_can_manage_question(answer_option.question_id)

        # Блокируем родителя
        question = await self.uow.questions.get_for_update(answer_option.question_id)
        if question is None:
            raise QuestionNotFoundError('Question not found.')

        has_attempts = await self.uow.question_attempts.exists_by_question_id(question.id)
        if has_attempts:
            raise QuestionAlreadyUsedError('Question already has student attempts and cannot be changed safely.')

        siblings = await self.uow.answer_options.get_by_ids(question.answer_option_ids)

        answer_option = next((item for item in siblings if item.id == command.answer_option_id), None)
        if answer_option is None:
            raise AnswerOptionNotFoundError('Answer option not found.')

        siblings_without_update_item = [item for item in siblings if item.id != answer_option.id]
        check_insert_position(siblings_without_update_item, command.position)
        old_position = answer_option.position

        answer_option.update(
            text=command.text,
            position=command.position,
            is_correct=command.is_correct,
        )

        await self.uow.answer_options.update_many(move_position(siblings_without_update_item, old_position, command.position))
        await self.uow.answer_options.update(answer_option)
        await self.uow.commit()

        return answer_option