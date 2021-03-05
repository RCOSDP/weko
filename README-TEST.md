# Running tests locally

## Running with venv

### Install python 3.5.x

I recommend 3.5.9, but older versions may work as well.
To install it you can use pyenv.
It is personal preference,
but I also like to create venv so I can easily delete it and recreate if needed.

```shell
pyenv install 3.5.9
pyenv global 3.5.9
python -m venv venv
pyenv global system
source venv/bin/activate
```

### Install python dependencies

```shell
python -m pip install -U setuptools wheel pip
python -m pip install -r packages.txt
python -m pip install -r packages-invenio.txt
sed -E 's/\/code\///g' requirements-weko-modules.txt | xargs python -m pip install
python -m pip install 'pytest>=4.6.4,<5.0.0' 'coverage>=4.5.3,<5.0.0' 'mock==3.0.5' 'moto==1.3.5' pytest-cov pytest-invenio responses
```

### Run the tests

#### Run all modules

```shell
./run-tests.sh
```

#### Run single module

```shell
python -m pytest modules/weko-bulkupdate
# OR
cd modules/weko-bulkupdate && python setup.py test
```

#### Run single test

```shell
python -m pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

## Running inside docker container

### Adjust file permissions

First of all,
we need to adjust the file permissions of the source code.

Because of `pytest-cov`,
we need write access to the weko folder.
At the time I write this,
by default there is no write access inside the docker container.
So the first step is to adjust this.

To check if there is write access inside the docker container,
try running the following command:

```shell
docker-compose exec web touch test.txt
```

If it doesn't fail for you,
probably there is no need to change any files permission.

Inside the docker container,
the user is `invenio`, group `invenio`.
The group `invenio` is GID 1000.
On your development server,
you have to join a group with GID 1000.
Use the command `getent group` to list groups.
Lets suppose the the group `centos` is GID 1000.
Then you have to run the following command:

```shell
gpasswd -a weko-devXX centos
```

You have to logoff and login to apply this change.

After that,
you must update the source code files and folders access permission.
`cd` to your weko folder and then:

```shell
chown -R weko-devXX:centos .
chmod g+w .
```

### Install test packages

Run the following command to install test packages inside your docker container.

```shell
docker-compose exec web sh -c "pip install 'pytest>=4.6.4,<5.0.0' 'coverage>=4.5.3,<5.0.0' 'mock==3.0.5' 'moto==1.3.5' pytest-cov pytest-invenio responses"
```

### Run the tests

#### Run all modules

```shell
docker-compose exec web ./run-tests.sh
```

#### Run single module

```shell
docker-compose exec web pytest modules/weko-bulkupdate
# OR
docker-compose exec web sh -c 'cd modules/weko-bulkupdate && python setup.py test'
```

#### Run single test

```shell
docker-compose exec web pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

### Known errors

If after running the tests,
you receive an error like

```
INTERNALERROR> sqlite3.OperationalError: unable to open database file
```

It means that you don't have write access inside the docker container.
Follow the steps written at the beginning of this manual.
