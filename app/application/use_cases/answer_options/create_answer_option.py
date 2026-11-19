from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.exceptions import QuestionNotFoundError, QuestionAlreadyUsedError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities.answer_option import AnswerOption
from app.domain.ordering import check_insert_position, make_room


@dataclass(slots=True)
class CreateAnswerOptionCommand:
    question_id: UUID
    text: str
    position: int
    is_correct: bool = False


class CreateAnswerOptionUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: CreateAnswerOptionCommand) -> AnswerOption:
        await self.access.ensure_can_manage_question(command.question_id)

        question = await self.uow.questions.get_for_update(command.question_id)
        if question is None:
            raise QuestionNotFoundError('Question not found.')

        has_attempts = await self.uow.question_attempts.exists_by_question_id(question.id)
        if has_attempts:
            raise QuestionAlreadyUsedError('Question already has student attempts and cannot be changed safely.')

        sibling_answers = await self.uow.answer_options.get_by_ids(question.answer_option_ids)
        check_insert_position(sibling_answers, command.position)
        await self.uow.answer_options.update_many(make_room(sibling_answers, command.position))

        answer_option = AnswerOption(
            id=uuid4(),
            question_id=command.question_id,
            text=command.text,
            position=command.position,
            is_correct=command.is_correct,
        )

        question.add_answer_option(answer_option.id)
        await self.uow.answer_options.add(answer_option)
        await self.uow.questions.update(question)
        await self.uow.commit()
        return answer_option