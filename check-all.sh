#!/bin/sh

python3 -m isort $1
python3 -m pycodestyle $1
python3 -m pydocstyle $1