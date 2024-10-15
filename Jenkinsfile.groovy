pipeline {
    agent any

    environment {
        // GCP Service Account Key (uploaded to Jenkins)
        GOOGLE_APPLICATION_CREDENTIALS = credentials('gcp-jenkins-key')
        // Terraform variables
        TF_VAR_project_id = 'your-gcp-project-id'
        TF_VAR_region     = 'us-central1'
        TF_VAR_cluster_name = 'jenkins-gke-cluster'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'git-credentials-id',
                    url: 'git@github.com:your-repo/your-project.git'
            }
        }

        stage('Terraform Init') {
            steps {
                withCredentials([file(credentialsId: 'gcp-jenkins-key', variable: 'GCP_KEY')]) {
                    sh '''
                        export GOOGLE_APPLICATION_CREDENTIALS=$GCP_KEY
                        terraform init
                    '''
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                input message: 'Approve Terraform Apply?', ok: 'Apply'
                withCredentials([file(credentialsId: 'gcp-jenkins-key', variable: 'GCP_KEY')]) {
                    sh '''
                        export GOOGLE_APPLICATION_CREDENTIALS=$GCP_KEY
                        terraform apply -auto-approve
                    '''
                }
            }
        }

        stage('Configure kubectl') {
            steps {
                withCredentials([file(credentialsId: 'gcp-jenkins-key', variable: 'GCP_KEY')]) {
                    sh '''
                        export GOOGLE_APPLICATION_CREDENTIALS=$GCP_KEY
                        gcloud auth activate-service-account --key-file=$GCP_KEY
                        gcloud container clusters get-credentials ${TF_VAR_cluster_name} --region ${TF_VAR_region} --project ${TF_VAR_project_id}
                    '''
                }
            }
        }

        stage('Deploy to GKE') {
            steps {
                sh '''
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // Implement your testing steps here
                sh 'echo "Running tests..."'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Deployment to GKE succeeded!'
            // Add notifications (e.g., email, Slack) if desired
        }
        failure {
            echo 'Deployment to GKE failed.'
            // Add notifications (e.g., email, Slack) if desired
        }
    }
}
