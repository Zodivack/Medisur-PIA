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

        stage('Despliegue y pruebas de humo en Kubernetes') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'kubeconfig-medisur',
                        variable: 'KUBECONFIG_FILE'
                    )
                ]) {
                    script {
                        def actualizacionAplicada = false

                        try {
                            sh '''
                                set -eu

                                echo "Actualizando la imagen del Deployment..."

                                kubectl --kubeconfig="$KUBECONFIG_FILE" \
                                    --namespace=medisur \
                                    set image deployment/medisur-api \
                                    medisur-api="$IMAGE_NAME:$IMAGE_TAG_VERSION"

                                echo "Imagen actualizada correctamente."
                            '''

                            actualizacionAplicada = true

                            sh '''
                                set -eu

                                BASE_URL="http://10.0.1.5"

                                echo "Esperando que termine el rollout..."

                                kubectl --kubeconfig="$KUBECONFIG_FILE" \
                                    --namespace=medisur \
                                    rollout status deployment/medisur-api \
                                    --timeout=180s

                                echo "Esperando la propagacion de los endpoints..."
                                sleep 5

                                echo "Prueba de humo: /health"

                                curl --fail --silent --show-error --max-time 10 \
                                    "$BASE_URL/health"

                                echo

                                echo "Prueba de humo: /ready"

                                curl --fail --silent --show-error --max-time 10 \
                                    "$BASE_URL/ready"

                                echo

                                echo "Prueba de humo: /version"

                                VERSION_VERIFICADA=0
                                INTENTO=1
                                MAX_INTENTOS=12

                                while [ "$INTENTO" -le "$MAX_INTENTOS" ] && [ "$VERSION_VERIFICADA" -eq 0 ]; do

                                    echo "Verificando version: intento $INTENTO de $MAX_INTENTOS"

                                    if VERSION_JSON=$(curl --fail --silent --show-error \
                                        --max-time 10 "$BASE_URL/version"); then

                                        printf '%s\\n' "$VERSION_JSON"

                                        if printf '%s' "$VERSION_JSON" | python3 -c '
import json
import sys

try:
    respuesta = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError) as error:
    print(f"Respuesta JSON invalida: {error}")
    sys.exit(1)

sha_esperado = sys.argv[1]
version_esperada = sys.argv[2]

sha_obtenido = respuesta.get("commit")
version_obtenida = respuesta.get("version")

print(f"SHA esperado: {sha_esperado}")
print(f"SHA recibido: {sha_obtenido}")
print(f"Version esperada: {version_esperada}")
print(f"Version recibida: {version_obtenida}")

if sha_obtenido != sha_esperado:
    print("La respuesta corresponde a otro commit.")
    sys.exit(1)

if version_obtenida != version_esperada:
    print("La version recibida no coincide.")
    sys.exit(1)

print("La version desplegada coincide con la imagen construida.")
' "$GIT_SHA" "$APP_VERSION"; then

                                            VERSION_VERIFICADA=1

                                        else
                                            echo "La respuesta todavia no corresponde a la nueva version."
                                        fi

                                    else
                                        echo "No se pudo consultar /version en este intento."
                                    fi

                                    if [ "$VERSION_VERIFICADA" -eq 0 ]; then
                                        if [ "$INTENTO" -lt "$MAX_INTENTOS" ]; then
                                            echo "Esperando 5 segundos antes de reintentar..."
                                            sleep 5
                                        fi

                                        INTENTO=$((INTENTO + 1))
                                    fi
                                done

                                if [ "$VERSION_VERIFICADA" -ne 1 ]; then
                                    echo "ERROR: No se pudo confirmar la version y SHA desplegados."
                                    exit 1
                                fi

                                echo "Pruebas de humo completadas correctamente."
                            '''

                        } catch (Exception error) {

                            if (actualizacionAplicada) {
                                echo "ERROR: fallo el despliegue o una prueba de humo."
                                echo "Intentando restaurar la revision anterior..."

                                def resultadoRollback = sh(
                                    returnStatus: true,
                                    script: '''
                                        set -eu

                                        echo "Ejecutando kubectl rollout undo..."

                                        kubectl --kubeconfig="$KUBECONFIG_FILE" \
                                            --namespace=medisur \
                                            rollout undo deployment/medisur-api

                                        echo "Esperando la recuperacion de la revision anterior..."

                                        kubectl --kubeconfig="$KUBECONFIG_FILE" \
                                            --namespace=medisur \
                                            rollout status deployment/medisur-api \
                                            --timeout=180s

                                        echo "Version restaurada:"

                                        curl --fail --silent --show-error \
                                            --max-time 10 http://10.0.1.5/version

                                        echo
                                    '''
                                )

                                if (resultadoRollback == 0) {
                                    echo "Rollback completado correctamente."
                                } else {
                                    echo "ERROR: no se pudo confirmar el rollback. Codigo: ${resultadoRollback}"
                                }

                            } else {
                                echo "La actualizacion del Deployment no se completo correctamente."
                                echo "No se ejecuta rollback porque no se confirmo un cambio de imagen."
                            }

                            throw error
                        }
                    }
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
