from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.exceptions import SectionNotFoundError
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.course_access import CourseAccessService
from app.domain.entities import Lecture
from app.domain.entities.question import Question, QuestionType
from app.domain.ordering import check_insert_position, make_room


@dataclass(slots=True)
class CreateQuestionCommand:
    section_id: UUID
    text: str
    position: int
    question_type: QuestionType
    max_attempts: int
    reward_points: int


class CreateQuestionUseCase:
    def __init__(self, uow: UnitOfWork, access: CourseAccessService) -> None:
        self.uow = uow
        self.access = access

    async def execute(self, command: CreateQuestionCommand) -> Question:
        await self.access.ensure_can_manage_section(command.section_id)

        section = await self.uow.sections.get_for_update(command.section_id)
        if section is None:
            raise SectionNotFoundError('Section not found.')

        # Необходимо обновить позиции не только лекций, но и вопросов
        sibling_lectures = await self.uow.lectures.get_by_ids(section.lecture_ids)
        sibling_questions = await self.uow.questions.get_by_ids(section.question_ids)
        siblings = sibling_lectures + sibling_questions

        check_insert_position(siblings, command.position)
        siblings_positions_updated = make_room(siblings, command.position)

        # Отделяем лекции и обновляем только лекции
        lecture_position_updated = [lecture for lecture in siblings_positions_updated if isinstance(lecture, Lecture)]
        await self.uow.lectures.update_many(lecture_position_updated)

        # Отделяем вопросы и обновляем только вопросы
        question_position_updated = [question for question in siblings_positions_updated if isinstance(question, Question)]
        await self.uow.questions.update_many(question_position_updated)

        question = Question(
            id=uuid4(),
            section_id=command.section_id,
            text=command.text,
            position=command.position,
            question_type=command.question_type,
            max_attempts=command.max_attempts,
            reward_points=command.reward_points,
        )

        section.add_question(question.id)
        await self.uow.questions.add(question)
        await self.uow.sections.update(section)
        await self.uow.commit()

        return question