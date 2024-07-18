..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


Configuration
=============

.. automodule:: invenio_iiif.config
   :members:

Invenio-IIIF depends heavily on `Flask-IIIF <https://flask-iiif.rtfd.io/en/latest/>`_
module for images transformation. Configurations related to images formats, resize and caching are
provided by ``Flask-IIIF``:

 - `IIIF_RESIZE_RESAMPLE <https://flask-iiif.readthedocs.io/en/latest/#flask_iiif.config.IIIF_RESIZE_RESAMPLE>`_
    Specifies the algorithm used to resample the image. The default one is `PIL.image.BICUBIC`
 - `IIIF_CACHE_HANDLER <https://flask-iiif.readthedocs.io/en/latest/#flask_iiif.config.IIIF_CACHE_HANDLER>`_
    Specifices how to cache thumbnails, e.g. in memory, Redis or any custom implementation.
 - `IIIF_CACHE_TIME <https://flask-iiif.readthedocs.io/en/latest/#flask_iiif.config.IIIF_CACHE_TIME>`_
    Specifies for how long images will be cached.
 - `IIIF_FORMATS <https://flask-iiif.readthedocs.io/en/latest/#flask_iiif.config.IIIF_FORMATS>`_
    Specifies the supported images formats and associated MIME types

