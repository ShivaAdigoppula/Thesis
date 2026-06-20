pipeline {
    agent any

    parameters {
        string(
            name: 'CODE_FILE',
            defaultValue: 'sample_codes/sample_01.py',
            description: 'Code file to review'
        )

        string(
            name: 'EC2_HOURLY_PRICE',
            defaultValue: '0.000',
            description: 'Enter EC2 hourly price for c6a.2xlarge'
        )
    }

    environment {
        ENVIRONMENT_NAME = 'ec2-c6a-2xlarge'
    }

    stages {
        stage('Checkout Code from GitHub') {
            steps {
                checkout scm
            }
        }

        stage('Verify Ollama') {
            steps {
                sh '''
                    echo "Checking Ollama..."
                    curl -s http://localhost:11434/api/tags
                    ollama list
                '''
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Code Review') {
            steps {
                sh '''
                    . venv/bin/activate

                    python3 review_all_models.py \
                      --code-file "${CODE_FILE}" \
                      --ec2-hourly-price "${EC2_HOURLY_PRICE}" \
                      --environment "${ENVIRONMENT_NAME}"
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/**/*, reviews/**/*', fingerprint: true, allowEmptyArchive: true
        }
    }
}
