node('x86_64')
{
    stage('checkout')
    {
        dir('pando-core') {
            checkout scm
        }
    }

    dir('pando-core')
    {
        gitlabCommitStatus
        {
            stage('build')
            {
                sh 'make coverage'
            }
        }
    }
}
