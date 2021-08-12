import json

from flask import request
from flask import Response
from sword3common.constants import JSON_LD_CONTEXT


def jsonld_serializer(data, **kwargs):
    kwargs.setdefault("mimetype", "application/ld+json")
    data = {
        "@context": JSON_LD_CONTEXT,
        "@id": data.get("@id") or request.url,
        **data,
    }
    return Response(json.dumps(data, indent=2) + "\n", **kwargs)
