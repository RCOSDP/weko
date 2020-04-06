# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""


from flask.signals import Namespace

_signals = Namespace()


#: Sent when a new item created.
item_created = _signals.signal('item_created')
