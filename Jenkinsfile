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
