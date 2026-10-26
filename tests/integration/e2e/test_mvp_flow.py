import pytest
from sqlalchemy import select, func

from app.infrastructure.database.models import CourseModel, ModuleModel, SectionModel, LectureModel


async def test_mvp_flow_from_login_to_public_read(client, seeded_admin_user):
    login_response = await client.post(
        '/api/auth/login',
        json={
            'email': 'admin@example.com',
            'password': 'strongpassword123',
        },
    )
    assert login_response.status_code == 200
    access_token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}


    course_response = await client.post(
        '/api/admin/courses',
        headers=headers,
        json={
            'title': 'FastAPI course',
            'description': 'Clean architecture in practice.',
        },
    )
    assert course_response.status_code == 201
    course_id = course_response.json()['id']

    module_response = await client.post(
        f'/api/admin/courses/{course_id}/modules',
        headers=headers,
        json={
            'title': 'MVP stage',
            'description': 'Content, users and access.',
            'position': 1,
        },
    )
    assert module_response.status_code == 201
    module_id = module_response.json()['id']

    section_response = await client.post(
        f'/api/admin/modules/{module_id}/sections',
        headers=headers,
        json={
            'title': 'Auth section',
            'description': 'JWT and route protection.',
            'position': 1,
        },
    )
    assert section_response.status_code == 201
    section_id = section_response.json()['id']

    lecture_response = await client.post(
        f'/api/admin/sections/{section_id}/lectures',
        headers=headers,
        json={
            'title': 'Bearer token in practice',
            'content': 'Lecture content',
            'position': 1,
        },
    )
    assert lecture_response.status_code == 201
    lecture_id = lecture_response.json()['id']

    courses_response = await client.get('/api/courses')
    assert courses_response.status_code == 200
    assert len(courses_response.json()) == 1

    structure_response = await client.get(f'/api/courses/{course_id}/structure')
    assert structure_response.status_code == 200
    structure_payload = structure_response.json()
    assert len(structure_payload['modules']) == 1
    assert len(structure_payload['modules'][0]['sections']) == 1
    assert len(structure_payload['modules'][0]['sections'][0]['lectures']) == 1

    lecture_read_response = await client.get(f'/api/lectures/{lecture_id}')
    assert lecture_read_response.status_code == 200
    assert lecture_read_response.json()['content'] == 'Lecture content'


    response_delete_lecture = await client.delete(f'/api/admin/lectures/{lecture_id}', headers=headers)
    assert response_delete_lecture.status_code == 204

    response_get_lectures = await client.get(f'/api/lectures/{lecture_id}')
    assert response_get_lectures.status_code == 404
    assert response_get_lectures.json()['error'] == 'lecture_not_found'
    assert response_get_lectures.json()['message'] == 'Lecture not found.'

    structure_response = await client.get(f'/api/courses/{course_id}/structure')
    structure_payload = structure_response.json()
    assert len(structure_payload['modules'][0]['sections'][0]['lectures']) == 0

    response_delete_section = await client.delete(f'/api/admin/sections/{section_id}', headers=headers)
    assert response_delete_section.status_code == 204

    structure_response = await client.get(f'/api/courses/{course_id}/structure')
    structure_payload = structure_response.json()
    assert len(structure_payload['modules'][0]['sections']) == 0

    response_delete_module = await client.delete(f'/api/admin/modules/{module_id}', headers=headers)
    assert response_delete_module.status_code == 204

    structure_response = await client.get(f'/api/courses/{course_id}/structure')
    structure_payload = structure_response.json()
    assert len(structure_payload['modules']) == 0

    response_delete_course = await client.delete(f'/api/admin/courses/{course_id}', headers=headers)
    assert response_delete_course.status_code == 204

    response_get_course = await client.get(f'/api/courses/{course_id}')
    assert response_get_course.status_code == 404
    assert response_get_course.json()['error'] == 'course_not_found'
    assert response_get_course.json()['message'] == 'Course not found.'



async def test_delete_course_removes_whole_tree(client, admin_auth_headers, seeded_course_tree, session_factory):
    response = await client.delete(f'/api/admin/courses/{seeded_course_tree.course_id}', headers=admin_auth_headers)
    assert response.status_code == 204

    async with session_factory() as session:
        for model in (CourseModel, ModuleModel, SectionModel, LectureModel):
            count = await session.scalar(select(func.count()).select_from(model))
            assert count == 0, f'в таблице {model.__tablename__} остались записи'





