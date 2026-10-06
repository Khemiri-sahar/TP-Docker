"""
Visit-Counter : application web du TP Docker.

Affiche le nombre de visites (stocke dans Redis) et l'identifiant du
conteneur qui repond a la requete, ce qui permet de verifier le scaling
(docker compose up -d --scale web=3).
"""

import os
import socket

import redis
from flask import Flask

# --- Configuration via variables d'environnement (voir docker-compose.yml) ---
# Par defaut on vise "db-service", le nom du conteneur Redis sur le reseau
# app-network : la resolution DNS est assuree par le bridge Docker.
REDIS_HOST = os.environ.get("REDIS_HOST", "db-service")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

app = Flask(__name__)

# decode_responses=True : les valeurs renvoyees sont des str et non des bytes.
cache = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=2,
)

# Identifiant du conteneur : Docker fixe le hostname au container ID court.
CONTAINER_ID = os.environ.get("HOSTNAME", socket.gethostname())


@app.route("/")
def index():
    """Incremente la cle 'hits' et affiche le compteur + l'ID du conteneur."""
    try:
        hits = cache.incr("hits")
    except redis.exceptions.RedisError as err:
        # Redis peut etre indisponible au demarrage (ordre de boot) ou supprime
        # pendant le test de robustesse : on renvoie une erreur lisible (503)
        # au lieu d'une stacktrace.
        return (
            "<h1>Service indisponible</h1>"
            f"<p>Impossible de joindre Redis sur {REDIS_HOST}:{REDIS_PORT}</p>"
            f"<p>Detail : {err}</p>",
            503,
        )

    return (
        "<h1>Bonjour !</h1>"
        f"<p>Cette page a ete vue <strong>{hits}</strong> fois.</p>"
        f"<p>Je suis le conteneur <code>{CONTAINER_ID}</code></p>"
    )


@app.route("/health")
def health():
    """Sonde simple : verifie que Redis repond au PING."""
    try:
        cache.ping()
    except redis.exceptions.RedisError:
        return "redis unreachable", 503
    return "ok", 200


if __name__ == "__main__":
    # host=0.0.0.0 : indispensable pour etre joignable depuis l'hote,
    # sinon Flask n'ecoute que sur la loopback du conteneur.
    app.run(host="0.0.0.0", port=5000)
