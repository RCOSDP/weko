# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Sanitized Unicode string field."""

from ftfy import fix_text

from .trimmedstring import TrimmedString


class SanitizedUnicode(TrimmedString):
    """String field that sanitizes and fixes problematic unicode characters."""

    UNWANTED_CHARACTERS = {
        # Zero-width space
        "\u200b",
    }

    def is_valid_xml_char(self, char):
        """Check if a character is valid based on the XML specification."""
        codepoint = ord(char)
        return (
            0x20 <= codepoint <= 0xD7FF
            or codepoint in (0x9, 0xA, 0xD)
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        )

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize sanitized string value."""
        value = super()._deserialize(value, attr, data, **kwargs)
        value = fix_text(value)

        # NOTE: This `join` might be ineffiecient... There's a solution with a
        # large compiled regex lying around, but needs a lot of tweaking.
        value = "".join(filter(self.is_valid_xml_char, value))
        for char in self.UNWANTED_CHARACTERS:
            value = value.replace(char, "")
        return value
