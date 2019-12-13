# PADKP-server
Simple DKP display and CRUD operations


##Development Instructions
(On windows)
* Install Python 3.7 and pip.
* python -m pip install Django
* python -m pip install djangorestframework
* from powershell or other tty (gitbash doesn't play nice here)
  * py manage.py migrate
  * py manage.py createsuperuser (provide username, email, and password for a local admin account)
  * py manage.py runserver
* login to localhost:8000/admin

