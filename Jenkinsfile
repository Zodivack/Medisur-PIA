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
                        --volume "$WORKSPACE:/workspace" \
                        --workdir /workspace \
                        python:3.12-slim \
                        sh -c '
                            python -m venv /tmp/venv &&
                            /tmp/venv/bin/python -m pip install --no-cache-dir -r requirements-dev.txt &&
                            /tmp/venv/bin/python -m pytest --junitxml=reports/pytest.xml
                        '
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
