import pytest

@pytest.fixture
def mock_agent(monkeypatch):
    class Job: id = 'mock'
    from liquidcore.config import agent
    monkeypatch.setattr(agent, 'launch', lambda *args: Job)
