pipeline {
    agent {
        label 'bb5'
    }
    parameters {
        string(name: 'SPACK_BRANCH', defaultValue: 'develop',
               description: 'Which branch of spack to use.')
        string(name: 'NEURON_BRANCH', defaultValue: '',
               description: 'Which branch of neuron to use. For master branch (neuron@develop) leave this parameter blank.')
    }

    environment {
        HOME = "${WORKSPACE}"
        JENKINS_DIR = "${WORKSPACE}/.jenkins"
    }

    stages {

        stage('install Spack'){
            steps {
                sh 'source $WORKSPACE/.jenkins/spack_setup.sh'
            }
        }

        stage('spack install neuron+debug@develop'){
            steps {
                sh 'sh $WORKSPACE/.jenkins/install_neuron.sh'
            }
        }
    }



    post {
        always {
            cleanWs()
        }
    }
}