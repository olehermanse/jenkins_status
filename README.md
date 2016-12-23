
Example:
```
$ python3 jenkins_status.py ci.cfengine.com
Build passed: testing-enterprise-3.10.x
$ python3 jenkins_status.py ci.cfengine.com --running
Running jobs:

$ python3 jenkins_status.py ci.cfengine.com --loop --verbose
Jenkins URL matches: 'https://ci.cfengine.com'.
Read previous status from 'jenkins_jobs.json' succesfully.
```
