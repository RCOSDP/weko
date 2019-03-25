#!/usr/bin/env bash
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# Check docs and sort source files in each module

exit_code=0

for mod_dir in "modules/"*
do
    inner_dir=${mod_dir#*/} # Get module name from path
    pydocstyle "$mod_dir/$inner_dir" "$mod_dir/tests" "$mod_dir/docs"
    isort "$mod_dir" -rc -c -df

    # Let isort run through entire code before stopping TravisCI
    if [ $? -ne 0 ]; then
        exit_code=1
    fi
done

exit $exit_code
