from uuid import uuid4

import pytest

from app.application.dto.course_structure import CourseStructureDTO, ModuleStructureDTO, SectionStructureDTO, LectureStructureDTO
from app.application.use_cases.courses.get_course import GetCourseUseCase, GetCourseQuery
from app.application.use_cases.courses.get_course_structure import GetCourseStructureUseCase, GetCourseStructureQuery
from app.application.use_cases.courses.get_courses import GetCoursesUseCase, GetCoursesQuery
from app.application.use_cases.lectures.get_lecture import GetLectureUseCase, GetLectureQuery
from app.domain.entities import Course
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section


@pytest.mark.asyncio
async def test_get_course_by_id(uow):
    course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    await uow.courses.add(course)

    use_case = GetCourseUseCase(uow.courses)

    result = await use_case.execute(
        GetCourseQuery(course_id=course.id)
    )

    assert result == course


@pytest.mark.asyncio
async def test_get_courses(uow):
    first_course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    await uow.courses.add(first_course)

    second_course = Course(id=uuid4(), title="SQLAlchemy course", description="ORM in practice.")
    await uow.courses.add(second_course)

    use_case = GetCoursesUseCase(uow.courses)
    result = await use_case.execute(GetCoursesQuery())

    assert result == [first_course, second_course]



@pytest.mark.asyncio
async def test_get_course_structure(uow):

    course = Course(id=uuid4(), title="FastAPI course", description="Clean architecture in practice.")
    module_first = Module(id=uuid4(), course_id=course.id, title="Module 1", description="Module description", position=1)
    section_first = Section(id=uuid4(), module_id=module_first.id, title="Section 1", description="Section description", position=1)
    lecture_first = Lecture(id=uuid4(), section_id=section_first.id, title="Lecture 1", content="First lecture", position=1)

    module_second = Module(id=uuid4(), course_id=course.id, title="Module 2", description="Module 2 description", position=2)
    section_second = Section(id=uuid4(), module_id=module_first.id, title="Section 2", description="Section 2 description", position=2)
    lecture_second = Lecture(id=uuid4(), section_id=section_first.id, title="Lecture 2", content="Lecture 2 description", position=2)

    course.module_ids.extend([module_second.id, module_first.id])
    module_first.section_ids.extend([section_second.id, section_first.id])
    section_first.lecture_ids.extend([lecture_second.id, lecture_first.id])

    await uow.courses.add(course)
    await uow.modules.add(module_second)
    await uow.sections.add(section_second)
    await uow.lectures.add(lecture_second)
    await uow.modules.add(module_first)
    await uow.sections.add(section_first)
    await uow.lectures.add(lecture_first)


    use_case = GetCourseStructureUseCase(
        uow.courses,
        uow.modules,
        uow.sections,
        uow.lectures,
    )

    result = await use_case.execute(GetCourseStructureQuery(course_id=course.id))

    structure = CourseStructureDTO(
        id=course.id,
        title=course.title,
        description=course.description,
        modules=[
            ModuleStructureDTO(
                id=module_first.id,
                title=module_first.title,
                description=module_first.description,
                position=module_first.position,
                sections=[
                    SectionStructureDTO(
                        id=section_first.id,
                        title=section_first.title,
                        description=section_first.description,
                        position=section_first.position,
                        lectures=[
                            LectureStructureDTO(
                                id=lecture_first.id,
                                title=lecture_first.title,
                                position=lecture_first.position
                            ),
                            LectureStructureDTO(
                                id=lecture_second.id,
                                title=lecture_second.title,
                                position=lecture_second.position
                            )
                        ]
                    ),
                    SectionStructureDTO(
                        id=section_second.id,
                        title=section_second.title,
                        description=section_second.description,
                        position=section_second.position,
                        lectures=[]
                    )
                ]
            ),
            ModuleStructureDTO(
                id=module_second.id,
                title=module_second.title,
                description=module_second.description,
                position=module_second.position,
                sections=[])
        ]
    )

    assert structure == result



@pytest.mark.asyncio
async def test_get_lecture(uow):
    lecture = Lecture(id=uuid4(), section_id=uuid4(), title="Lecture 1", content="First lecture", position=1)
    await uow.lectures.add(lecture)

    use_case = GetLectureUseCase(uow.lectures)

    result = await use_case.execute(GetLectureQuery(lecture_id=lecture.id))

    assert lecture == result







