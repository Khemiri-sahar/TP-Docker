// Pipeline CI/CD du TP "Visit-Counter".
//
// Declenchement : un webhook GitHub/GitLab (configure cote repo, voir README)
// appelle Jenkins a chaque push. Le trigger ci-dessous active l'ecoute de ce
// webhook ; en l'absence de webhook (reseau ferme), remplacer par :
//     triggers { pollSCM('H/5 * * * *') }
pipeline {
    agent any

    options {
        // Evite les builds concurrents sur la meme branche
        disableConcurrentBuilds()
        timestamps()
    }

    triggers {
        githubPush()
    }

    environment {
        // Les identifiants Docker Hub ne sont PAS exposes ici : ils sont
        // limites a l'etape de push (withCredentials) pour que le code
        // execute pendant l'installation et les tests n'y ait pas acces.
        IMAGE_NAME = "counter-app"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Install dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --no-cache-dir -r requirements-dev.txt
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            // On ne construit/publie l'image que depuis la branche principale.
            // expression{} fonctionne aussi bien en job "Pipeline" classique
            // (GIT_BRANCH = "origin/main") qu'en Multibranch Pipeline
            // (BRANCH_NAME = "main"), contrairement a branch 'main' qui est
            // reserve au Multibranch.
            when {
                expression {
                    return env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH in ['main', 'origin/main']
                }
            }
            steps {
                sh 'docker build -t "$IMAGE_NAME:$IMAGE_TAG" .'
            }
        }

        stage('Push to Docker Hub') {
            when {
                expression {
                    return env.BRANCH_NAME == 'main' ||
                           env.GIT_BRANCH in ['main', 'origin/main']
                }
            }
            steps {
                // Identifiants Jenkins : Manage Jenkins > Credentials >
                // ID "dockerhub-credentials", type "Username with password".
                // Simples quotes : le shell (et non Groovy) developpe les
                // variables, le mot de passe n'apparait donc pas dans le script.
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                                  usernameVariable: 'DOCKERHUB_USR',
                                                  passwordVariable: 'DOCKERHUB_PSW')]) {
                    sh '''
                        echo "$DOCKERHUB_PSW" | docker login -u "$DOCKERHUB_USR" --password-stdin
                        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKERHUB_USR/$IMAGE_NAME:$IMAGE_TAG"
                        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKERHUB_USR/$IMAGE_NAME:latest"
                        docker push "$DOCKERHUB_USR/$IMAGE_NAME:$IMAGE_TAG"
                        docker push "$DOCKERHUB_USR/$IMAGE_NAME:latest"
                        docker logout
                        docker image rm "$DOCKERHUB_USR/$IMAGE_NAME:$IMAGE_TAG" "$DOCKERHUB_USR/$IMAGE_NAME:latest" || true
                    '''
                }
            }
        }
    }

    post {
        always {
            // Nettoyage : supprime les images locales taguees par ce build
            // pour ne pas saturer le disque de l'agent Jenkins
            sh 'docker image rm "$IMAGE_NAME:$IMAGE_TAG" || true'
            cleanWs()
        }
        success {
            echo "Pipeline OK : image publiee sur Docker Hub sous le tag ${IMAGE_TAG} et latest."
        }
        failure {
            echo "Pipeline en echec : voir les logs des etapes ci-dessus."
        }
    }
}
