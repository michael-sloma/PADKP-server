# PADKP-server
Simple DKP display and CRUD operations


##Development Instructions
(On windows)
* Install Python 3.7 and pip.
* py -m pip install Django==2.2.7
* py -m pip install djangorestframework==3.10.3
* py -m pip install pytz
* py -m pip install setuptools
* for VSCode linting:
  * pip install pylint-django
  * preferences -> "python.linting.pylintArgs": [ "--load-plugins=pylint_django" ]

* from powershell or other tty (gitbash doesn't play nice here)
  * py manage.py migrate
  * py manage.py createsuperuser (provide username, email, and password for a local admin account)
  * py manage.py runserver
* login to localhost:8000/admin

##Deploying Migrations
* connect to server
* py manage.py makemigrations
* py manage.py migrate

##Running Commands
* py manage.py command_name

##Running Tests
* py manage.py test
