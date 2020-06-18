# Running tests locally

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
docker-compose exec web sh -c 'pip install -U pytest && pip install coverage==4.5.4 pytest==5.4.3 pytest-cov pytest-invenio mock responses'
```

### Run the tests

#### Run all modules

```shell
docker-compose exec web ./run-tests.sh
```

#### Run single module

```shell
docker-compose exec web pytest modules/weko-bulkupdate
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
