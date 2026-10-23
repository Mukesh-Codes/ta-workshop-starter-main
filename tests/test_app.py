import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task list before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker and priority selector."""
    response = client.get('/')

    assert response.status_code == 200
    assert b"Task Tracker" in response.data
    assert b'value="Low"' in response.data
    assert b'value="Medium"' in response.data
    assert b'value="High"' in response.data


def test_get_tasks(client):
    """Return every task with a default priority."""
    response = client.get('/api/tasks')

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_with_each_priority(client):
    """Create tasks successfully with each supported priority."""
    for priority in ('Low', 'Medium', 'High'):
        response = client.post(
            '/api/tasks',
            json={"title": f"{priority} task", "priority": priority}
        )

        assert response.status_code == 201
        assert response.get_json()['priority'] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Use Medium when a new task omits its priority."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_empty_priority_to_medium(client):
    """Use Medium when a new task has an empty priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_rejects_invalid_priority(client):
    """Reject priorities outside the supported values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": "Urgent"}
    )

    assert response.status_code == 400
    assert response.get_json()['error'] == (
        'Priority must be Low, Medium, or High'
    )


def test_add_task_missing_title(client):
    """Reject tasks without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200

    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2


def test_frontend_renders_priority_class(client):
    """Expose the priority rendering behavior in the frontend script."""
    with open('static/app.js', encoding='utf-8') as script_file:
        script = script_file.read()

    assert 'task.priority' in script
    assert 'priority-${priority.toLowerCase()}' in script
    assert 'JSON.stringify({ title, priority })' in script
