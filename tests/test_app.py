import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Create a Flask test client."""
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
    """Render the task tracker and its priority controls."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data
    assert b'id="task-priority"' in response.data
    assert b'value="Low"' in response.data
    assert b'value="Medium"' in response.data
    assert b'value="High"' in response.data


def test_get_tasks(client):
    """Return existing tasks with the Medium priority default."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert [task['priority'] for task in data] == ['Medium', 'Medium']


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_with_priority(client, priority):
    """Create a task for each supported priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Prioritized task", "priority": priority}
    )
    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Default an omitted priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Default task"})
    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_empty_priority_to_medium(client):
    """Default an empty priority to Medium."""
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
    assert "Priority" in response.get_json()['error']


def test_add_task_rejects_non_string_priority(client):
    """Reject non-string priority values with a validation error."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": []}
    )
    assert response.status_code == 400
    assert "Priority" in response.get_json()['error']


def test_get_tasks_returns_created_priority(client):
    """Return a created task priority from the GET endpoint."""
    client.post(
        '/api/tasks',
        json={"title": "High priority task", "priority": "High"}
    )
    response = client.get('/api/tasks')
    created_task = response.get_json()[-1]
    assert created_task['title'] == 'High priority task'
    assert created_task['priority'] == 'High'


def test_frontend_renders_priority_labels(client):
    """Expose frontend code that renders returned task priorities."""
    response = client.get('/static/app.js')
    assert response.status_code == 200
    assert b'priorityLabel.textContent = priority' in response.data
    assert b"'Medium'" in response.data


def test_add_task_missing_title(client):
    """Reject task creation when the title is missing."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
