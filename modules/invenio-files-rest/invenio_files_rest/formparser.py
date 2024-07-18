# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Werkzeug form data parser customization."""

from werkzeug import exceptions
from werkzeug.formparser import FormDataParser as WerkzeugFormDataParser


class FormDataParser(WerkzeugFormDataParser):
    """Custom form data parser."""

    def parse(self, stream, mimetype, content_length, options=None):
        """Parse the information from the given request.

        :param stream: An input stream.
        :param mimetype: The mimetype of the data.
        :param content_length: The content length of the incoming data.
        :param options: Optional mimetype parameters (used for
                        the multipart boundary for instance).
        :return: A tuple in the form ``(stream, form, files)``.
        """
        if options is None:
            options = {}

        parse_func = self.get_parse_func(mimetype, options)
        if parse_func is not None:
            # Check content length only if we are actually going to parse
            # the data.
            if (
                self.max_content_length is not None
                and content_length is not None
                and content_length > self.max_content_length
            ):
                raise exceptions.RequestEntityTooLarge()

            try:
                return parse_func(self, stream, mimetype, content_length, options)
            except ValueError:
                if not self.silent:
                    raise

        return stream, self.cls(), self.cls()
