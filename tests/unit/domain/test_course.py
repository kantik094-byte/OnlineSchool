from uuid import uuid4

import pytest

from app.domain.entities import Course
from app.domain.exceptions import InvalidCourseError


def test_course_is_created_with_valid_data() -> None:
    course = Course(
        id=uuid4(),
        title='FastAPI course',
        description='Clean architecture in practice.',
    )

    assert course.title == 'FastAPI course'
    assert course.description == 'Clean architecture in practice.'
    assert course.module_ids == []



def test_add_module_to_course() -> None:
    course = Course(
        id=uuid4(),
        title='FastAPI course',
        description='Clean architecture in practice.',
    )

    module_id = uuid4()
    course.add_module(module_id)

    assert len(course.module_ids) == 1
    assert module_id in course.module_ids



def test_remove_module_from_course() -> None:
    course = Course(
        id=uuid4(),
        title='FastAPI course',
        description='Clean architecture in practice.',
    )

    module_id = uuid4()
    course.add_module(module_id)

    course.remove_module(module_id)

    assert len(course.module_ids) == 0


def test_remove_module_raises_error_when_module_id_is_not_exist() -> None:
    course = Course(
        id=uuid4(),
        title='FastAPI course',
        description='Clean architecture in practice.',
    )

    module_id = uuid4()
    course.add_module(module_id)

    deleting_module_id = uuid4()

    with pytest.raises(InvalidCourseError):
        course.remove_module(deleting_module_id)

    assert len(course.module_ids) == 1
    assert module_id in course.module_ids



def test_course_raises_error_when_title_is_blank() -> None:
    with pytest.raises(InvalidCourseError):
        Course(
            id=uuid4(),
            title='    ',
            description='Clean architecture in practice.',
        )


def test_course_raises_error_when_description_is_blank() -> None:
    with pytest.raises(InvalidCourseError):
        Course(
            id=uuid4(),
            title='FastAPI course',
            description='    ',
        )


def test_course_update_changes_state() -> None:
    course = Course(
        id=uuid4(),
        title='Old title',
        description='Old description',
    )

    course.update(title='New title', description='New description')

    assert course.title == 'New title'
    assert course.description == 'New description'