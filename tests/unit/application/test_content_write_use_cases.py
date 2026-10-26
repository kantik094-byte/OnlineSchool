from uuid import uuid4

import pytest

from app.application.exceptions import CourseNotFoundError, CourseModuleNotFoundError, SectionNotFoundError, LectureNotFoundError, \
    AccessDeniedError, AuthenticationError
from app.application.use_cases.courses.create_course import CreateCourseUseCase, CreateCourseCommand
from app.application.use_cases.courses.delete_course import DeleteCourseUseCase, CourseDeleteCommand
from app.application.use_cases.courses.update_course import UpdateCourseUseCase, UpdateCourseCommand
from app.application.use_cases.lectures.create_lecture import CreateLectureUseCase, CreateLectureCommand
from app.application.use_cases.lectures.delete_lecture import DeleteLectureUseCase, DeleteLectureCommand
from app.application.use_cases.lectures.update_lecture import UpdateLectureUseCase, UpdateLectureCommand
from app.application.use_cases.modules.create_module import CreateModuleUseCase, CreateModuleCommand
from app.application.use_cases.modules.delete_module import DeleteModuleUseCase, DeleteModuleCommand
from app.application.use_cases.modules.update_module import UpdateModuleUseCase, UpdateModuleCommand
from app.application.use_cases.sections.create_sections import CreateSectionUseCase, CreateSectionCommand
from app.application.use_cases.sections.delete_section import DeleteSectionUseCase, DeleteSectionCommand
from app.application.use_cases.sections.update_section import UpdateSectionUseCase, UpdateSectionCommand
from app.domain.entities import Course, UserRole
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section
from app.domain.exceptions import InvalidPositionError
from tests.unit.support.assertions import positions
from tests.unit.support.fakes import FakeIdentityProvider





"================================================== Course =================================================="

async def test_create_course_adds_course_and_commits_by_admin(uow, users) -> None:

    use_case = CreateCourseUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    result = await use_case.execute(
        CreateCourseCommand(
            title="FastAPI course",
            description="Clean architecture in practice.",
        )
    )

    assert result.id in uow.courses.items
    assert result.title == "FastAPI course"
    assert result.description == "Clean architecture in practice."
    assert uow.committed is True




async def test_delete_course_by_admin(uow, content, users):

    course = await content.course()

    use_case = DeleteCourseUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    await use_case.execute(CourseDeleteCommand(course_id=course.id))

    assert uow.courses.items == {}
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_delete_course_by_student_and_anon(uow, users, content, caller, exception):
    course = await content.course()
    user = users.get_student() if caller == "student" else None

    use_case = DeleteCourseUseCase(uow=uow, idp=FakeIdentityProvider(user))
    with pytest.raises(exception):
        await use_case.execute(CourseDeleteCommand(course_id=course.id))

    assert course.id in uow.courses.items
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_course_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = CreateCourseUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateCourseCommand(
                title="FastAPI course",
                description="Clean architecture in practice.",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False




async def test_update_course_changes_existing_course_by_admin(uow, users, content) -> None:

    course = await content.course(title="Old", description="Old description")

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        UpdateCourseCommand(
            course_id=course.id,
            title="New",
            description="New description",
        )
    )

    assert result.title == "New"
    assert result.description == "New description"
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_course_changes_existing_course_by_student_and_anon(uow, users, content, caller,
                                                                                  exception) -> None:

    user = users.get_student() if caller == "student" else None

    course = await content.course(title="Old", description="Old description")

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=course.id,
                title="New",
                description="New description",
            )
        )

    course_in_storage = await uow.courses.get_by_id(course.id)

    assert course_in_storage.title == course.title
    assert course_in_storage.description == course.description



async def test_update_course_raises_not_found_when_course_is_missing(uow, users) -> None:

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(CourseNotFoundError):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=uuid4(),
                title="New",
                description="New description",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_course_when_course_is_missing_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = UpdateCourseUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateCourseCommand(
                course_id=uuid4(),
                title="New",
                description="New description",
            )
        )

    assert uow.courses.items == {}
    assert uow.committed is False




"================================================== Module =================================================="

async def test_create_module_adds_module_to_course_and_commits(uow, users, content) -> None:

    course = await content.course()

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        CreateModuleCommand(
            course_id=course.id,
            title="Module 1",
            description="Module description",
            position=1,
        )
    )

    assert result.id in uow.modules.items
    assert result.id in course.module_ids
    assert uow.committed is True




async def test_add_module_with_existing_position(uow, users, content) -> None:
    course = await content.course()
    module_first = await content.module(course)
    module_second = await content.module(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_module = await use_case.execute(CreateModuleCommand(course_id=course.id, title="Module 1", description="Module description", position=1))

    assert len(uow.modules.items) == 3
    assert uow.modules.items[new_module.id].position == 1
    assert uow.modules.items[module_first.id].position == 2
    assert uow.modules.items[module_second.id].position == 3
    assert new_module.id in course.module_ids
    assert uow.committed is True



async def test_add_module_n_plus_1(uow, users, content) -> None:
    course = await content.course()
    module_first = await content.module(course)
    module_second = await content.module(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_module = await use_case.execute(CreateModuleCommand(course_id=course.id, title="Module 1", description="Module description", position=3))

    assert len(uow.modules.items) == 3
    assert uow.modules.items[module_first.id].position == 1
    assert uow.modules.items[module_second.id].position == 2
    assert uow.modules.items[new_module.id].position == 3
    assert new_module.id in course.module_ids
    assert uow.committed is True



async def test_negative_add_module_n_plus_2(uow, users, content) -> None:
    course = await content.course()
    await content.module(course)
    await content.module(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(InvalidPositionError):
        await use_case.execute(CreateModuleCommand(course_id=course.id, title="Module 1", description="Module description", position=4))



@pytest.mark.parametrize(
    ("moved", "new_position", "expected"),
    [
        ("Module 1", 3, ["Module 2", "Module 3", "Module 1"]),
        ("Module 1", 2, ["Module 2", "Module 1", "Module 3"]),
        ("Module 2", 1, ["Module 2", "Module 1", "Module 3"]),
        ("Module 2", 3, ["Module 1", "Module 3", "Module 2"]),
        ("Module 3", 1, ["Module 3", "Module 1", "Module 2"]),
        ("Module 3", 2, ["Module 1", "Module 3", "Module 2"]),
        ("Module 2", 2, ["Module 1", "Module 2", "Module 3"]),
    ],
    ids=["1->3", "1->2", "2->1", "2->3", "3->1", "3->2", "2->2 same place"],
)
async def test_update_module_position(uow, users, content, moved, new_position, expected) -> None:
    course = await content.course()
    modules = {m.title: m for m in [await content.module(course) for _ in range(3)]}
    target = modules[moved]

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(UpdateModuleCommand(
        module_id=target.id, title=target.title, description=target.description, position=new_position,
    ))

    assert positions(uow.modules, course.module_ids) == [(title, i) for i, title in enumerate(expected, start=1)]



async def test_negative_update_module_position_out_of_range(uow, users, content) -> None:
    course = await content.course()
    modules = [await content.module(course) for _ in range(3)]

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    with pytest.raises(InvalidPositionError):
        await use_case.execute(UpdateModuleCommand(
            module_id=modules[0].id, title=modules[0].title, description=modules[0].description, position=4,
        ))

    assert positions(uow.modules, course.module_ids) == [("Module 1", 1), ("Module 2", 2), ("Module 3", 3)]



@pytest.mark.parametrize(
    ("deleted", "expected"),
    [
        ("Module 1", ["Module 2", "Module 3"]),
        ("Module 2", ["Module 1", "Module 3"]),
        ("Module 3", ["Module 1", "Module 2"]),
    ]
)
async def test_delete_module(uow, users, content, deleted, expected) -> None:
    course = await content.course()
    modules = {m.title: m for m in [await content.module(course) for _ in range(3)]}
    target = modules[deleted]

    use_case = DeleteModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(DeleteModuleCommand(module_id=target.id))

    assert positions(uow.modules, course.module_ids) == [(title, i) for i, title in enumerate(expected, start=1)]

    assert target.id not in uow.modules.items
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_delete_module_by_student_and_anon(uow, users, content, caller, exception):
    course = await content.course()
    module = await content.module(course)
    user = users.get_student() if caller == "student" else None

    use_case = DeleteModuleUseCase(uow=uow, idp=FakeIdentityProvider(user))
    with pytest.raises(exception):
        await use_case.execute(DeleteModuleCommand(module_id=module.id))

    assert module.id in uow.modules.items
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_module_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    course = Course(id=uuid4(), title="Course", description="Description")
    await uow.courses.add(course)

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateModuleCommand(
                course_id=course.id,
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



async def test_create_module_raises_not_found_when_course_is_missing(uow, users) -> None:

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(CourseNotFoundError):
        await use_case.execute(
            CreateModuleCommand(
                course_id=uuid4(),
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_module_when_course_is_missing_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = CreateModuleUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateModuleCommand(
                course_id=uuid4(),
                title="Module 1",
                description="Module description",
                position=1,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False



async def test_update_module_changes_existing_module(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(
        course,
        title="Old module",
        description="Old description",
        position=1,
    )

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        UpdateModuleCommand(
            module_id=module.id,
            title="New module",
            description="New description",
            position=1,
        )
    )

    assert result.title == "New module"
    assert result.description == "New description"
    assert result.position == 1
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_module_changes_existing_module_by_student_and_anon(uow, users, caller, exception, content) -> None:

    user = users.get_student() if caller == "student" else None

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Old module",
        description="Old description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateModuleCommand(
                module_id=module.id,
                title="New module",
                description="New description",
                position=2,
            )
        )

    module_in_storage = await uow.modules.get_by_id(module.id)

    assert module_in_storage.title == module.title
    assert module_in_storage.description == module.description
    assert module_in_storage.position == module.position



async def test_update_module_raises_not_found_when_module_is_missing(uow, users) -> None:

    use_case = UpdateModuleUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(CourseModuleNotFoundError):
        await use_case.execute(
            UpdateModuleCommand(
                module_id=uuid4(),
                title="New module",
                description="New description",
                position=2,
            )
        )

    assert uow.modules.items == {}
    assert uow.committed is False






"================================================== Section =================================================="

async def test_create_section_adds_section_to_module_and_commits(uow, users) -> None:

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Module",
        description="Description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        CreateSectionCommand(
            module_id=module.id,
            title="Section 1",
            description="Section description",
            position=1,
        )
    )

    assert result.id in uow.sections.items
    assert result.id in module.section_ids
    assert uow.committed is True




async def test_create_section_with_existing_position(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section_first = await content.section(module)
    section_second = await content.section(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_section = await use_case.execute(CreateSectionCommand(module_id=module.id, title="Section 1", description="Section description", position=1))

    assert len(uow.sections.items) == 3
    assert uow.sections.items[new_section.id].position == 1
    assert uow.sections.items[section_first.id].position == 2
    assert uow.sections.items[section_second.id].position == 3
    assert new_section.id in module.section_ids
    assert uow.committed is True



async def test_add_section_n_plus_1(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section_first = await content.section(module)
    section_second = await content.section(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_section = await use_case.execute(CreateSectionCommand(module_id=module.id, title="Section 1", description="Section description", position=3))

    assert len(uow.sections.items) == 3
    assert uow.sections.items[section_first.id].position == 1
    assert uow.sections.items[section_second.id].position == 2
    assert uow.sections.items[new_section.id].position == 3
    assert new_section.id in module.section_ids
    assert uow.committed is True



async def test_negative_add_section_n_plus_2(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    await content.section(module)
    await content.section(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(InvalidPositionError):
        await use_case.execute(CreateSectionCommand(module_id=module.id, title="Section 1", description="Section description", position=4))




@pytest.mark.parametrize(
    ("moved", "new_position", "expected"),
    [
        ("Section 1", 3, ["Section 2", "Section 3", "Section 1"]),
        ("Section 1", 2, ["Section 2", "Section 1", "Section 3"]),
        ("Section 2", 1, ["Section 2", "Section 1", "Section 3"]),
        ("Section 2", 3, ["Section 1", "Section 3", "Section 2"]),
        ("Section 3", 1, ["Section 3", "Section 1", "Section 2"]),
        ("Section 3", 2, ["Section 1", "Section 3", "Section 2"]),
        ("Section 2", 2, ["Section 1", "Section 2", "Section 3"]),
    ],
    ids=["1->3", "1->2", "2->1", "2->3", "3->1", "3->2", "2->2 same place"],
)
async def test_update_section_position(uow, users, content, moved, new_position, expected) -> None:
    course = await content.course()
    module = await content.module(course)
    sections = {s.title: s for s in [await content.section(module) for _ in range(3)]}
    target = sections[moved]

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(
        UpdateSectionCommand(
            section_id=target.id,
            title=target.title,
            description=target.description,
            position=new_position
        )
    )

    assert positions(uow.sections, module.section_ids) == [(title, i) for i, title in enumerate(expected, start=1)]



async def test_negative_update_section_position_out_of_range(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    sections = [await content.section(module) for _ in range(3)]

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    with pytest.raises(InvalidPositionError):
        await use_case.execute(UpdateSectionCommand(
            section_id=sections[0].id, title=sections[0].title, description=sections[0].description, position=4,
        ))

    assert positions(uow.sections, module.section_ids) == [("Section 1", 1), ("Section 2", 2), ("Section 3", 3)]



@pytest.mark.parametrize(
    ("deleted", "expected"),
    [
        ("Section 1", ["Section 2", "Section 3"]),
        ("Section 2", ["Section 1", "Section 3"]),
        ("Section 3", ["Section 1", "Section 2"]),
    ]
)
async def test_delete_section(uow, users, content, deleted, expected) -> None:
    course = await content.course()
    module = await content.module(course)
    sections = {m.title: m for m in [await content.section(module) for _ in range(3)]}
    target = sections[deleted]

    use_case = DeleteSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(DeleteSectionCommand(section_id=target.id))

    assert positions(uow.sections, module.section_ids) == [(title, i) for i, title in enumerate(expected, start=1)]

    assert target.id not in uow.sections.items
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_delete_section_by_student_and_anon(uow, users, content, caller, exception):
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    user = users.get_student() if caller == "student" else None

    use_case = DeleteSectionUseCase(uow=uow, idp=FakeIdentityProvider(user))
    with pytest.raises(exception):
        await use_case.execute(DeleteSectionCommand(section_id=section.id))

    assert section.id in uow.sections.items
    assert uow.committed is False


@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_section_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    module = Module(
        id=uuid4(),
        course_id=uuid4(),
        title="Module",
        description="Description",
        position=1,
    )
    await uow.modules.add(module)

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateSectionCommand(
                module_id=module.id,
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



async def test_create_section_raises_not_found_when_module_is_missing(uow, users) -> None:

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(CourseModuleNotFoundError):
        await use_case.execute(
            CreateSectionCommand(
                module_id=uuid4(),
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_section_when_module_is_missing_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = CreateSectionUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateSectionCommand(
                module_id=uuid4(),
                title="Section 1",
                description="Section description",
                position=1,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False




async def test_update_section_changes_existing_section(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(
        module,
        title="Old section",
        description="Old description",
        position=1,
    )

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        UpdateSectionCommand(
            section_id=section.id,
            title="New section",
            description="New description",
            position=1,
        )
    )

    assert result.title == "New section"
    assert result.description == "New description"
    assert result.position == 1
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_section_changes_existing_section_by_student_and_anon(uow, users, content, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    course = await content.course()
    module = await content.module(course)
    section = await content.section(
        module,
        title="Old section",
        description="Old description",
        position=1,
    )

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=section.id,
                title="New section",
                description="New description",
                position=1,
            )
        )

    section_in_storage = await uow.sections.get_by_id(section.id)

    assert section_in_storage.title == section.title
    assert section_in_storage.description == section.description
    assert section_in_storage.position == section.position




async def test_update_section_raises_not_found_when_section_is_missing(uow, users) -> None:

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(SectionNotFoundError):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=uuid4(),
                title="New section",
                description="New description",
                position=2,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_section_when_section_is_missing_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = UpdateSectionUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateSectionCommand(
                section_id=uuid4(),
                title="New section",
                description="New description",
                position=2,
            )
        )

    assert uow.sections.items == {}
    assert uow.committed is False





"================================================== Section =================================================="

async def test_create_lecture_adds_lecture_to_section_and_commits(uow, users) -> None:

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Section",
        description="Description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        CreateLectureCommand(
            section_id=section.id,
            title="Lecture 1",
            content="Lecture content",
            position=1,
        )
    )

    assert result.id in uow.lectures.items
    assert result.id in section.lecture_ids
    assert uow.committed is True




async def test_create_lecture_with_existing_position(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lecture_first = await content.lecture(section)
    lecture_second = await content.lecture(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_lecture = await use_case.execute(CreateLectureCommand(section_id=section.id, title="Section 1", content="Lecture content", position=1))

    assert len(uow.lectures.items) == 3
    assert uow.lectures.items[new_lecture.id].position == 1
    assert uow.lectures.items[lecture_first.id].position == 2
    assert uow.lectures.items[lecture_second.id].position == 3
    assert new_lecture.id in section.lecture_ids
    assert uow.committed is True



async def test_add_lecture_n_plus_1(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lecture_first = await content.lecture(section)
    lecture_second = await content.lecture(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    new_lecture = await use_case.execute(CreateLectureCommand(section_id=section.id, title="Section 1", content="Lecture content", position=3))

    assert len(uow.lectures.items) == 3
    assert uow.lectures.items[lecture_first.id].position == 1
    assert uow.lectures.items[lecture_second.id].position == 2
    assert uow.lectures.items[new_lecture.id].position == 3

    assert new_lecture.id in section.lecture_ids
    assert uow.committed is True



async def test_negative_add_lecture_n_plus_2(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    await content.lecture(section)
    await content.lecture(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(InvalidPositionError):
        await use_case.execute(CreateLectureCommand(section_id=section.id, title="Section 1", content="Lecture content", position=4))


@pytest.mark.parametrize(
    ("moved", "new_position", "expected"),
    [
        ("Lecture 1", 3, ["Lecture 2", "Lecture 3", "Lecture 1"]),
        ("Lecture 1", 2, ["Lecture 2", "Lecture 1", "Lecture 3"]),
        ("Lecture 2", 1, ["Lecture 2", "Lecture 1", "Lecture 3"]),
        ("Lecture 2", 3, ["Lecture 1", "Lecture 3", "Lecture 2"]),
        ("Lecture 3", 1, ["Lecture 3", "Lecture 1", "Lecture 2"]),
        ("Lecture 3", 2, ["Lecture 1", "Lecture 3", "Lecture 2"]),
        ("Lecture 2", 2, ["Lecture 1", "Lecture 2", "Lecture 3"]),
    ],
    ids=["1->3", "1->2", "2->1", "2->3", "3->1", "3->2", "2->2 same place"],
)
async def test_update_lecture_position(uow, users, content, moved, new_position, expected) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lectures = {l.title: l for l in [await content.lecture(section) for _ in range(3)]}
    target = lectures[moved]

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(
        UpdateLectureCommand(
            lecture_id=target.id,
            title=target.title,
            content=target.content,
            position=new_position
        )
    )

    assert positions(uow.lectures, section.lecture_ids) == [(title, i) for i, title in enumerate(expected, start=1)]



async def test_negative_update_lecture_position_out_of_range(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lectures = [await content.lecture(section) for _ in range(3)]

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    with pytest.raises(InvalidPositionError):
        await use_case.execute(UpdateLectureCommand(
            lecture_id=lectures[0].id, title=lectures[0].title, content=lectures[0].content, position=4,
        ))

    assert positions(uow.lectures, section.lecture_ids) == [("Lecture 1", 1), ("Lecture 2", 2), ("Lecture 3", 3)]


@pytest.mark.parametrize(
    ("deleted", "expected"),
    [
        ("Lecture 1", ["Lecture 2", "Lecture 3"]),
        ("Lecture 2", ["Lecture 1", "Lecture 3"]),
        ("Lecture 3", ["Lecture 1", "Lecture 2"]),
    ]
)
async def test_delete_lecture(uow, users, content, deleted, expected) -> None:
    course = await content.course()
    module = await content.module(course)
    secton = await content.section(module)
    lectures = {l.title: l for l in [await content.lecture(secton) for _ in range(3)]}
    target = lectures[deleted]

    use_case = DeleteLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    await use_case.execute(DeleteLectureCommand(lecture_id=target.id))

    assert positions(uow.lectures, secton.lecture_ids) == [(title, i) for i, title in enumerate(expected, start=1)]

    assert target.id not in uow.lectures.items
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_delete_lecture_by_student_and_anon(uow, users, content, caller, exception):
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lecture = await content.lecture(section)
    user = users.get_student() if caller == "student" else None

    use_case = DeleteLectureUseCase(uow=uow, idp=FakeIdentityProvider(user))
    with pytest.raises(exception):
        await use_case.execute(DeleteLectureCommand(lecture_id=lecture.id))

    assert lecture.id in uow.lectures.items
    assert uow.committed is False


@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_lecture_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    section = Section(
        id=uuid4(),
        module_id=uuid4(),
        title="Section",
        description="Description",
        position=1,
    )
    await uow.sections.add(section)

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateLectureCommand(
                section_id=section.id,
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



async def test_create_lecture_raises_not_found_when_section_is_missing(uow, users) -> None:

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(SectionNotFoundError):
        await use_case.execute(
            CreateLectureCommand(
                section_id=uuid4(),
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_create_lecture_when_section_is_missing_by_student_and_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = CreateLectureUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            CreateLectureCommand(
                section_id=uuid4(),
                title="Lecture 1",
                content="Lecture content",
                position=1,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



async def test_update_lecture_changes_existing_lecture(uow, users, content) -> None:
    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lecture = await content.lecture(
        section,
        title="Old lecture",
        content="Old content",
        position=1,
    )

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))
    result = await use_case.execute(
        UpdateLectureCommand(
            lecture_id=lecture.id,
            title="New lecture",
            content="New content",
            position=1,
        )
    )

    assert result.title == "New lecture"
    assert result.content == "New content"
    assert result.position == 1
    assert uow.committed is True



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_lecture_changes_existing_lecture_by_student_anon(uow, users, content, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    course = await content.course()
    module = await content.module(course)
    section = await content.section(module)
    lecture = await content.lecture(
        section,
        title="Old lecture",
        content="Old content",
        position=1,
    )

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=lecture.id,
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    lecture_in_storage = await uow.lectures.get_by_id(lecture.id)

    assert lecture_in_storage.title == lecture.title
    assert lecture_in_storage.content == lecture.content
    assert lecture_in_storage.position == lecture.position



async def test_update_lecture_raises_not_found_when_lecture_is_missing(uow, users) -> None:

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(users.get_admin()))

    with pytest.raises(LectureNotFoundError):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=uuid4(),
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False



@pytest.mark.parametrize(("caller", "exception"), [("student", AccessDeniedError), ("anon", AuthenticationError)])
async def test_negative_update_lecture_when_lecture_is_missing_by_student_anon(uow, users, caller, exception) -> None:

    user = users.get_student() if caller == "student" else None

    use_case = UpdateLectureUseCase(uow=uow, idp=FakeIdentityProvider(user))

    with pytest.raises(exception):
        await use_case.execute(
            UpdateLectureCommand(
                lecture_id=uuid4(),
                title="New lecture",
                content="New content",
                position=2,
            )
        )

    assert uow.lectures.items == {}
    assert uow.committed is False