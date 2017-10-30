import pytest


@pytest.fixture
def mock_agent(monkeypatch):
    class Job: id = 'mock'
    from liquidcore.config import agent
    monkeypatch.setattr(agent, 'launch', lambda *args: Job)



@pytest.fixture(autouse=True)
def mock_should_welcome(monkeypatch):
    from liquidcore.welcome import views
    monkeypatch.setattr(views, 'should_welcome', lambda: False)
