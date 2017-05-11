pipeline {
	agent {
		label 'x86_64'
	}
	post {
	    failure {
	    	updateGitlabCommitStatus name: 'build', state: 'failed'
	    }
	    success {
	    	updateGitlabCommitStatus name: 'build', state: 'success'
	    }
	}
	options {
	    gitLabConnection('AVS GitLab')
	    buildDiscarder(logRotator(numToKeepStr:'10'))
	    skipDefaultCheckout()
	}
	triggers {
	    gitlab(triggerOnPush: true,
	    	   triggerOnMergeRequest: true,
	    	   triggerOpenMergeRequestOnPush: 'both',
	    	   branchFilterType: 'All')
	    pollSCM('H/10 * * * *')
	}
	stages {
		stage('checkout') {
			steps {
		        dir('pando-core') {
		            checkout scm
		        }
			}
	    }
		stage("build") {
			steps {
				dir('pando-core') {
					sh 'make coverage'
				}
			}
		}
	}
}
