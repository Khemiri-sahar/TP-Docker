# Image de base : Alpine est la variante la plus legere de l'image Python
# officielle (~50 Mo contre ~900 Mo pour l'image standard), ce qui reduit
# la surface d'attaque et accelere pull/push.
FROM python:3.11-alpine

# Dossier de travail dans le conteneur
WORKDIR /app

# Copier uniquement le fichier de dependances d'abord : tant que
# requirements.txt ne change pas, Docker reutilise le cache de ce layer
# et ne reinstalle pas les paquets a chaque modification de app.py.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code applicatif (invalide le cache uniquement a partir d'ici)
COPY app.py .

# Creer un utilisateur non-root et donner la propriete du dossier app
# -D : pas de mot de passe ; -u 1000 : UID fixe et previsible
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app

# Executer l'application avec cet utilisateur non-root (principe du moindre
# privilege : un breakout du conteneur n'offre pas les droits root sur l'hote)
USER appuser

# Port d'ecoute de l'application Flask
EXPOSE 5000

# Commande de demarrage du conteneur
CMD ["python", "app.py"]
