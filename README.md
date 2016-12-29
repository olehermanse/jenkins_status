
Example:
```
$ python3 jenkins_status.py ci.cfengine.com
Build started: yocto-integration
Job created: yoctobuild-standalone-master
Job created: yoctobuild-standalone-stable
$ python3 jenkins_status.py ci.cfengine.com
$ python3 jenkins_status.py ci.cfengine.com --running
Running jobs:
  yocto-integration
$ python3 jenkins_status.py ci.cfengine.com --loop --verbose
Jenkins URL matches: 'https://ci.cfengine.com'.
Read previous status from 'jenkins_jobs.json' succesfully.
```
