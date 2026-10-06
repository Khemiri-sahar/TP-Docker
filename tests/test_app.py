"""
Tests unitaires pour app.py.

On remplace le client Redis reel par fakeredis pour que les tests
s'executent sans dependre d'un serveur Redis externe (ce qui permet a
Jenkins de lancer "pytest" dans l'etape Build/Test, avant meme que
l'image Docker ne soit construite).
"""

import fakeredis
import pytest

import app as app_module


@pytest.fixture
def client(monkeypatch):
    # Remplace le client redis de l'application par un faux client en memoire
    fake_cache = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "cache", fake_cache)

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def test_index_increments_counter(client):
    """Chaque visite doit incrementer le compteur 'hits'."""
    first = client.get("/")
    assert first.status_code == 200
    assert b"vue <strong>1</strong> fois" in first.data

    second = client.get("/")
    assert b"vue <strong>2</strong> fois" in second.data


def test_index_shows_container_id(client):
    """La page doit afficher l'identifiant du conteneur (HOSTNAME)."""
    response = client.get("/")
    assert app_module.CONTAINER_ID.encode() in response.data


def test_health_ok_when_redis_reachable(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"ok"


def test_index_returns_503_when_redis_down(client, monkeypatch):
    """Si Redis est injoignable, l'app doit repondre 503 proprement."""

    class BrokenRedis:
        def incr(self, *_args, **_kwargs):
            raise app_module.redis.exceptions.ConnectionError("down")

        def ping(self):
            raise app_module.redis.exceptions.ConnectionError("down")

    monkeypatch.setattr(app_module, "cache", BrokenRedis())

    response = client.get("/")
    assert response.status_code == 503

    health = client.get("/health")
    assert health.status_code == 503
