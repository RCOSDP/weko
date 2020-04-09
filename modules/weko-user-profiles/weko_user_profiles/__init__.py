# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-user-profiles."""

from .api import current_userprofile
from .ext import WekoUserProfiles
from .models import AnonymousUserProfile, UserProfile
from .version import __version__

__all__ = ('__version__', 'WekoUserProfiles', 'AnonymousUserProfile',
           'UserProfile', 'current_userprofile')
