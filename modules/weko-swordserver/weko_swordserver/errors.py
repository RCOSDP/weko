# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Useful errors in weko-swordserver."""

from enum import Enum

class ErrorType(Enum):
    # Swordv3 ErrorType
    BadRequest                      = ("BadRequest",                    400, "BadRequest")
    ByReferenceFileSizeExceeded     = ("ByReferenceFileSizeExceeded",   400, "BadRequest")
    ContentMalformed                = ("ContentMalformed",              400, "BadRequest")
    InvalidSegmentSize              = ("InvalidSegmentSize",            400, "BadRequest")
    MaxAssembledSizeExceeded        = ("MaxAssembledSizeExceeded",      400, "BadRequest")
    SegmentLimitExceeded            = ("SegmentLimitExceeded",          400, "BadRequest")
    UnexpectedSegment               = ("UnexpectedSegment",             400, "BadRequest")
    AuthenticationRequired          = ("AuthenticationRequired",        401, "Unauthorized")
    AuthenticationFailed            = ("AuthenticationFailed",          403, "Forbidden")
    Forbidden                       = ("Forbidden",                     403, "Forbidden")
    MethodNotAllowed	            = ("MethodNotAllowed",              405, "MethodNotAllowed")
    SegmentedUploadTimedOut         = ("SegmentedUploadTimedOut",       410, "MethodNotAllowed")
    ByReferenceNotAllowed           = ("ByReferenceNotAllowed",         412, "PreconditionFailed")
    DigestMismatch                  = ("DigestMismatch",                412, "PreconditionFailed")
    ETagNotMatched                  = ("ETagNotMatched",                412, "PreconditionFailed")
    ETagRequired                    = ("ETagRequired",                  412, "PreconditionFailed")
    OnBehalfOfNotAllowed            = ("OnBehalfOfNotAllowed",          412, "PreconditionFailed")
    MaxUploadSizeExceeded           = ("MaxUploadSizeExceeded",         413, "PayloadTooLarge")
    ContentTypeNotAcceptable        = ("ContentTypeNotAcceptable",      415, "UnsupportedMediaType")
    FormatHeaderMismatch            = ("FormatHeaderMismatch",          415, "UnsupportedMediaType")
    MetadataFormatNotAcceptable     = ("MetadataFormatNotAcceptable",   415, "UnsupportedMediaType")
    PackagingFormatNotAcceptable    = ("PackagingFormatNotAcceptable",  415, "UnsupportedMediaType")

    # Addlitional ErrorType
    NotFound                        = ("NotFound",                      404, "NotFound")
    ServerError                     = ("ServerError",                   500, "InternalServerError")

    def __init__(self, type, code, httpName):
        self.type = type
        self.code = code
        self.httpName = httpName


class WekoSwordserverException(Exception):
    errorType = ErrorType.ServerError
    message = ""

    def __init__(self, msg=None, errorType=None, ex=None, **kwargs):
        """

        Initialize WekoSwordserverException.

        Args:
            msg (str): Error message.
            errorType (ErrorType): Error type.
            ex (Exception): Exception.
            **kwargs: Arbitrary keyword arguments.
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_swordserver."
        super(Exception, self).__init__(msg, **kwargs)
        self.message = msg
        if errorType is not None:
            self.errorType = errorType

