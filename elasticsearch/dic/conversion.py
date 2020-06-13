# -*- coding: utf-8 -*-
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

"""WEKO3 module docstring."""


def main():
    # path
    fcode = 'code/kui.txt'
    fcharacter = 'character/kui.txt'

    try:
        # Read
        dic_lines = []
        with open(fcode, 'r', encoding='utf-8') as fp:
            for line in fp.readlines():
                line = line.strip().split(',')
                if(len(line) == 2):
                    dic_line = ''
                    for code in line:
                        if dic_line == '':
                            dic_line = chr(int(code, 16))
                        else:
                            dic_line = dic_line + ' => ' + chr(int(code, 16))

                    dic_lines.append(dic_line)

        # Write
        with open(fcharacter, 'w', encoding='utf-8') as fp:
            fp.writelines('\n'.join(dic_lines))

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
