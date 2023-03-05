..
    This file is part of Invenio.
    Copyright (C) 2016-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======
Version 1.0.2 (released 2019-05-27)

- Allow Elasticsearch indexing arguments to be modified by subscribing to
  ``before_record_index`` signal.

Version 1.0.1 (released 2018-10-11)

- Allow forwarding arguments from ``RecordIndexer.process_bulk_queue`` to
  ``elasticsearch.helpers.bulk`` calls via the ``es_bulk_kwargs`` parameter.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
