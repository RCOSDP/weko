# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-indextree-journal."""
from .ext import WekoIndextreeJournal, WekoIndextreeJournalREST
from .version import __version__

__all__ = ('__version__', 'WekoIndextreeJournal', 'WekoIndextreeJournalREST')
