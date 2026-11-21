pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Pruebas y cobertura') {
            steps {
                sh '''
                    set -eu

                    mkdir -p reports

                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --env HOME=/tmp \
                        --volume "$WORKSPACE:$WORKSPACE" \
                        --workdir "$WORKSPACE" \
                        python:3.12-slim \
                        sh -c '
                            python -m venv /tmp/venv &&
                            /tmp/venv/bin/python -m pip install --no-cache-dir -r requirements-dev.txt &&
                            /tmp/venv/bin/python -m pytest --junitxml=reports/pytest.xml
                        '

                    test -s coverage.xml
                    test -s reports/pytest.xml

                    echo "Origenes del informe de cobertura:"
                    sed -n "/<sources>/,/<\\/sources>/p" coverage.xml
                '''
            }

            post {
                always {
                    junit(
                        allowEmptyResults: true,
                        testResults: 'reports/pytest.xml'
                    )
                }
            }
        }

        stage('Analisis SonarQube') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube-MediSur') {
                        sh "\"${scannerHome}/bin/sonar-scanner\""
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Validar acceso a Kubernetes') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'kubeconfig-medisur',
                        variable: 'KUBECONFIG_FILE'
                    )
                ]) {
                    sh '''
                        set -eu

                        echo "Validando acceso al namespace medisur..."

                        kubectl --kubeconfig="$KUBECONFIG_FILE" \
                            get deployments -n medisur

                        echo "Verificando permiso para actualizar deployments..."

                        PERMISO=$(kubectl --kubeconfig="$KUBECONFIG_FILE" \
                            auth can-i patch deployments -n medisur)

                        echo "Permiso para actualizar deployments: $PERMISO"

                        test "$PERMISO" = "yes"

                        echo "Acceso a Kubernetes validado correctamente."
                    '''
                }
            }
        }

        stage('Preparar metadatos de imagen') {
            steps {
                script {
                    def appVersion = readFile('VERSION').trim()

                    if (!(appVersion ==~ /^[0-9]+\.[0-9]+\.[0-9]+$/)) {
                        error(
                            'El archivo VERSION debe utilizar el formato X.Y.Z. Ejemplo: 1.0.0'
                        )
                    }

                    def gitSha = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    if (!(gitSha ==~ /^[0-9a-f]{40}$/)) {
                        error('No se pudo obtener un SHA completo valido del commit.')
                    }

                    def fechaConstruccion = sh(
                        script: 'date -u +%Y-%m-%dT%H:%M:%SZ',
                        returnStdout: true
                    ).trim()

                    env.APP_VERSION = appVersion
                    env.GIT_SHA = gitSha
                    env.GIT_SHA_SHORT = gitSha.take(7)
                    env.BUILD_DATE = fechaConstruccion

                    env.IMAGE_NAME = 'ghcr.io/zodivack/medisur-api'
                    env.IMAGE_TAG_VERSION = "${appVersion}-${env.GIT_SHA_SHORT}"
                    env.IMAGE_TAG_SHA = env.GIT_SHA_SHORT

                    echo "Version de la aplicacion: ${env.APP_VERSION}"
                    echo "SHA completo: ${env.GIT_SHA}"
                    echo "SHA corto: ${env.GIT_SHA_SHORT}"
                    echo "Fecha UTC: ${env.BUILD_DATE}"
                    echo "Imagen: ${env.IMAGE_NAME}"
                    echo "Etiqueta de version: ${env.IMAGE_TAG_VERSION}"
                    echo "Etiqueta SHA: ${env.IMAGE_TAG_SHA}"
                }
            }
        }

        stage('Construir imagen Docker') {
            steps {
                sh '''
                    set -eu

                    echo "Construyendo imagen Docker..."

                    docker build --pull \
                        --build-arg "APP_VERSION=$APP_VERSION" \
                        --build-arg "GIT_SHA=$GIT_SHA" \
                        --build-arg "BUILD_DATE=$BUILD_DATE" \
                        --tag "$IMAGE_NAME:$IMAGE_TAG_VERSION" \
                        --tag "$IMAGE_NAME:$IMAGE_TAG_SHA" \
                        .

                    echo "Verificando usuario de ejecucion de la imagen..."

                    USUARIO_CONTENEDOR=$(docker image inspect \
                        --format='{{.Config.User}}' \
                        "$IMAGE_NAME:$IMAGE_TAG_VERSION")

                    echo "Usuario configurado: $USUARIO_CONTENEDOR"

                    test "$USUARIO_CONTENEDOR" = "10001"

                    echo "Imagen construida y verificada correctamente."
                '''
            }
        }

        stage('Publicar imagen en GHCR') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'ghcr-credentials',
                        usernameVariable: 'GHCR_USERNAME',
                        passwordVariable: 'GHCR_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x
                        set -eu

                        trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT

                        echo "Autenticando en GitHub Container Registry..."

                        printf '%s' "$GHCR_TOKEN" | docker login ghcr.io \
                            --username "$GHCR_USERNAME" \
                            --password-stdin

                        echo "Publicando etiqueta de version..."

                        docker push "$IMAGE_NAME:$IMAGE_TAG_VERSION"

                        echo "Publicando etiqueta SHA..."

                        docker push "$IMAGE_NAME:$IMAGE_TAG_SHA"

                        echo "Imagen publicada correctamente en GHCR."
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'coverage.xml,reports/pytest.xml',
                allowEmptyArchive: true
            )
        }
    }
}
