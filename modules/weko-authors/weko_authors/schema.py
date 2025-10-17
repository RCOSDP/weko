# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.

"""Module of weko-authors."""


from datetime import datetime
from marshmallow import Schema, ValidationError, fields, validates_schema, post_load, validate


def validate_date(value):
    """Validate the date format is YYYY-MM-DD."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Not a valid date format. Use YYYY-MM-DD.")


class EmailInfoSchema(Schema):
    """Schema for author's email information."""

    email = fields.String()
    """Email of the author."""

    class Meta:
        strict = True


class AuthorIdInfoSchema(Schema):
    """Schema for author's identifier information."""

    idType = fields.String()
    """Type of identifier (e.g., WEKO, ORCID)."""

    authorId = fields.String()
    """Value of the identifier."""

    authorIdShowFlg = fields.String(validate=validate.OneOf(["true", "false"]))
    """Flag to indicate if the identifier should be displayed."""

    class Meta:
        strict = True

    @validates_schema
    def validate_author_id_pair(self, data, **kwargs):
        """Validate that both 'idType' and 'authorId' are provided together."""
        id_type = data.get("idType")
        author_id = data.get("authorId")
        if (id_type is None) != (author_id is None):
            raise ValidationError(
                "Both 'idType' and 'authorId' must be provided together."
            )


class AuthorNameInfoSchema(Schema):
    """Schema for author's name information."""

    language = fields.String()
    """Language code (e.g., 'en', 'ja')."""

    firstName = fields.String()
    """Author's first name."""

    familyName = fields.String()
    """Author's family name."""

    nameFormat = fields.String()
    """Format of the full name (e.g., 'familyNmAndNm')."""

    nameShowFlg = fields.String(validate=validate.OneOf(["true", "false"]))
    """Flag to indicate if the name should be displayed."""

    class Meta:
        strict = True

    @validates_schema
    def validate_language_required(self, data, **kwargs):
        """Ensure 'language' is set if name parts are provided."""
        if (data.get("firstName") or data.get("familyName")) and not data.get("language"):
            raise ValidationError(
                "If 'firstName' or 'familyName' is provided, 'language' must also be specified.",
                field_name="language")

    @post_load
    def set_default_name_format(self, data, **kwargs):
        """Set default 'nameFormat' if not provided."""
        if (
            data.get("language") and (data.get("firstName")
            and data.get("familyName") and not data.get("nameFormat"))
        ):
            data["nameFormat"] = "familyNmAndNm"
        return data


class IdentifierInfoSchema(Schema):
    """Schema for affiliation identifier information."""

    affiliationIdType = fields.String()
    """Type of the affiliation ID (e.g., GRID, ROR)."""

    affiliationId = fields.String()
    """Value of the affiliation identifier."""

    identifierShowFlg = fields.String(validate=validate.OneOf(["true", "false"]))
    """Flag to indicate if the identifier should be displayed."""

    class Meta:
        strict = True

    @validates_schema
    def validate_affiliation_id_pair(self, data, **kwargs):
        """Validate the affiliationIdType and affiliationId pair."""
        affiliationIdType = data.get("affiliationIdType")
        affiliationId = data.get("affiliationId")
        if (affiliationIdType is None) != (affiliationId is None):
            raise ValidationError(
                "Both 'affiliationIdType' and 'affiliationId' must be provided together."
            )


class AffiliationNameInfoSchema(Schema):
    """Schema for affiliation name information."""

    affiliationName = fields.String()
    """Name of the affiliation."""

    affiliationNameLang = fields.String()
    """Language code of the affiliation name."""

    affiliationNameShowFlg = fields.String(validate=validate.OneOf(["true", "false"]))
    """Flag to indicate if the name should be displayed."""

    class Meta:
        strict = True

    @validates_schema
    def validate_affiliation_name_pair(self, data, **kwargs):
        """Ensure both 'affiliationName' and 'affiliationNameLang' are provided together."""
        affiliationName = data.get("affiliationName")
        affiliationNameLang = data.get("affiliationNameLang")
        if (affiliationName is None) != (affiliationNameLang is None):
            raise ValidationError(
                "Both 'affiliationName' and 'affiliationNameLang' must be provided together."
            )


class AffiliationPeriodInfoSchema(Schema):
    """Schema for affiliation period information."""

    periodStart = fields.String(validate=validate_date)
    """Start date of the affiliation period (YYYY-MM-DD)."""

    periodEnd = fields.String(validate=validate_date)
    """End date of the affiliation period (YYYY-MM-DD)."""

    class Meta:
        strict = True

    @validates_schema
    def validate_period(self, data, **kwargs):
        """Validate the period start and end dates."""
        start_date = data.get("periodStart")
        end_date = data.get("periodEnd")
        if start_date and end_date and start_date > end_date:
            raise ValidationError("periodStart must be before periodEnd.")


class AffiliationInfoSchema(Schema):
    """Schema for full affiliation information."""

    identifierInfo = fields.List(fields.Nested(IdentifierInfoSchema))
    """List of identifier information related to the affiliation."""

    affiliationNameInfo = fields.List(fields.Nested(AffiliationNameInfoSchema))
    """List of names associated with the affiliation."""

    affiliationPeriodInfo = fields.List(fields.Nested(AffiliationPeriodInfoSchema))
    """List of periods during which the author was affiliated."""

    class Meta:
        strict = True


class AuthorSchema(Schema):
    """Schema for complete author information."""

    emailInfo = fields.List(fields.Nested(EmailInfoSchema))
    """List of email addresses associated with the author."""

    authorIdInfo = fields.List(fields.Nested(AuthorIdInfoSchema))
    """List of identifiers related to the author."""

    authorNameInfo = fields.List(fields.Nested(AuthorNameInfoSchema))
    """List of names for the author."""

    affiliationInfo = fields.List(fields.Nested(AffiliationInfoSchema))
    """List of affiliations associated with the author."""

    communityIds = fields.List(fields.String())

    class Meta:
        strict = True

    @validates_schema(skip_on_field_errors=True)
    def validate_not_empty(self, data, **kwargs):
        """Ensure the author schema is not empty."""
        if not data:
            raise ValidationError("author can not be null.")


class AuthorUpdateSchema(AuthorSchema):
    """Schema for updating author information."""

    @validates_schema
    def validate_weko_id_required(self, data, **kwargs):
        """Ensure at least one WEKO ID is included on update."""
        author_id_info = data.get("authorIdInfo", [])
        if not any(item.get("idType") == "WEKO" for item in author_id_info):
            raise ValidationError(
                "At least one WEKO ID must be provided in update.",
                field_name="authorIdInfo"
            )


class AuthorCreateRequestSchema(Schema):
    """Request schema for creating a new author."""

    author = fields.Nested(AuthorSchema, required=True)
    """Author information to be created."""

    class Meta:
        strict = True


class AuthorUpdateRequestSchema(Schema):
    """Request schema for updating an existing author."""

    force_change = fields.Bool()
    """Flag to force change"""

    author = fields.Nested(AuthorUpdateSchema, required=True)
    """Updated author information."""

    class Meta:
        strict = True
