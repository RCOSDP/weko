# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dictionary utilities."""


def clear_none(d):
    """Clear None values and empty dicts from a dict."""
    del_keys = []
    for k, v in d.items():
        if v is None:
            del_keys.append(k)
        elif isinstance(v, dict):
            clear_none(v)
            if v == {}:
                del_keys.append(k)
        elif isinstance(v, list):
            clear_none_list(v)
            if v == []:
                del_keys.append(k)

    # Delete the keys (cannot be done during the dict iteration)
    for k in del_keys:
        del d[k]


def clear_none_list(ls):
    """Clear values from a list (in-place)."""
    del_idx = []
    for i, v in enumerate(ls):
        if v is None:
            del_idx.append(i)
        elif isinstance(v, list):
            clear_none_list(v)
            if v == []:
                del_idx.append(i)
        elif isinstance(v, dict):
            clear_none(v)
            if v == {}:
                del_idx.append(i)

    # Delete the keys (reverse so index stays stable).
    for i in reversed(del_idx):
        del ls[i]


def parse_lookup_key(lookup_key):
    """Parse a lookup key."""
    if not lookup_key:
        raise KeyError("No lookup key specified")

    # Parse the list of keys
    if isinstance(lookup_key, str):
        keys = lookup_key.split(".")
    elif isinstance(lookup_key, list):
        keys = lookup_key
    else:
        raise TypeError("lookup must be string or list")

    return keys


def dict_lookup(source, lookup_key, parent=False):
    """Make a lookup into a dict based on a dot notation.

    Examples of the supported dot notation:

    - ``'a'`` - Equivalent to ``source['a']``
    - ``'a.b'`` - Equivalent to ``source['a']['b']``
    - ``'a.b.0'`` - Equivalent to ``source['a']['b'][0]`` (for lists)

    List notation is also supported:

    - `['a']``
    - ``['a','b']``
    - ``['a','b', 0]``

    :param source: The dictionary object to perform the lookup in.
    :param parent: If parent argument is True, returns the parent node of
                   matched object.
    :param lookup_key: A string using dot notation, or a list of keys.
    """
    # Copied from dictdiffer (CERN contributed part) and slightly modified.
    keys = parse_lookup_key(lookup_key)

    if parent:
        keys = keys[:-1]

    # Lookup the key
    value = source
    for key in keys:
        try:
            if isinstance(value, list):
                key = int(key)
            value = value[key]
        except (TypeError, IndexError, ValueError) as exc:
            raise KeyError(lookup_key) from exc
    return value


def dict_set(source, key, value):
    """Set a value into a dict via a dot-notated key.

    This also creates missing key "paths".

    Examples of the supported dot notation:

    - ``'a'`` - Equivalent to ``source['a'] = value``
    - ``'a.b'`` - Equivalent to ``source['a']['b'] = value``
    - ``'a.b.0'`` - Equivalent to ``source['a']['b'][0] = value`` (for lists)

    List notation is also supported:

    - `['a']``
    - ``['a','b']``
    - ``['a','b', 0]``

    :param source: The dictionary object to set the value in.
    :param key: A string using dot notation, or a list of keys.
    :param value: The value to be set.
    """
    keys = parse_lookup_key(key)
    parent = source
    for key in keys[:-1]:
        if isinstance(key, int):
            parent = parent[key]
        else:
            parent = parent.setdefault(key, {})
    parent[keys[-1]] = value


def dict_merge(dest, source):
    """Merges source into dest.

    It does not merge arrays of dicts.
    """
    for key in source:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(source[key], dict):
                dict_merge(dest[key], source[key])
        else:
            dest[key] = source[key]


def filter_dict_keys(src, keys):
    """Filter a dictionary based on a list of key paths."""
    # Split the keys into top-level and nested keys
    top_level_keys = [key for key in keys if "." not in key]
    nested_keys = [key for key in keys if "." in key]

    # Filter the top-level keys
    result = {key: src[key] for key in top_level_keys if key in src}

    # Handle nested keys
    for key in nested_keys:
        parts = key.split(".")
        current_dict = src
        for part in parts[:-1]:
            if part in current_dict:
                current_dict = current_dict[part]
            else:
                break  # Skip this key if the path does not exist
        # Update the filtered dictionary with the nested key if it exists
        if parts[-2] in result and parts[-1] in current_dict:
            if parts[-2] not in result:
                result[parts[-2]] = {}
            result[parts[-2]][parts[-1]] = current_dict[parts[-1]]

    # Handle specific case for top-level keys that are dictionaries but not explicitly mentioned
    for key in src:
        if key not in result and isinstance(src[key], dict):
            subkeys = [k.split(".", 1)[1] for k in keys if k.startswith(f"{key}.")]
            if subkeys:
                result[key] = filter_dict_keys(src[key], subkeys)

    return result
