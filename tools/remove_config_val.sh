#!/bin/bash

CONFIG_FILE="$1"
TARGET_KEY="$2"

if [ $# -ne 2 ]; then
    echo "Usage: $0 <config.py> <SETTING_NAME>"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "File not found: $CONFIG_FILE"
    exit 1
fi


awk -v key="$TARGET_KEY" '
BEGIN {
    skip = 0
    depth = 0
    comment = ""
}

# temporarily store comment lines
/^[[:space:]]*#/ {
    if (!skip) {
        comment = comment $0 "\n"
    }
    next
}

{
    # detect target setting
    if (!skip && $0 ~ "^[[:space:]]*" key "[[:space:]]*=") {

        skip = 1
        comment = ""

        line = $0

        # calculate bracket depth
        depth += gsub(/\[/,"[",line)
        depth += gsub(/\{/,"{",line)
        depth += gsub(/\(/,"(",line)

        depth -= gsub(/\]/,"]",line)
        depth -= gsub(/\}/,"}",line)
        depth -= gsub(/\)/,")",line)

        # one line value (string, number, boolean, etc.)
        if (depth <= 0) {
            skip = 0
            depth = 0
        }

        next
    }


    # remove multi-line value
    if (skip) {

        line = $0

        depth += gsub(/\[/,"[",line)
        depth += gsub(/\{/,"{",line)
        depth += gsub(/\(/,"(",line)

        depth -= gsub(/\]/,"]",line)
        depth -= gsub(/\}/,"}",line)
        depth -= gsub(/\)/,")",line)

        if (depth <= 0) {
            skip = 0
            depth = 0
        }

        next
    }


    # output non-deleted lines
    if (comment != "") {
        printf "%s", comment
        comment=""
    }

    print
}

END {
    if (comment != "") {
        printf "%s", comment
    }
}
' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" &&
mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"

echo "Removed $TARGET_KEY"