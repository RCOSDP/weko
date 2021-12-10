#!/bin/bash

sphinx-build -b gettext source/ build/gettext
sphinx-intl update -p build/gettext -l en
sphinx-intl update -p build/gettext -l ja
sphinx-build -b html source/ build/html/en -D language='en'
sphinx-build -b html source/ build/html/ja -D language='ja'

#schema2rst -c schema2rst_config.yml -o source/developer/database.rst

