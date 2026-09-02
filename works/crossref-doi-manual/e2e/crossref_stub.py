"""A local stand-in for the Crossref deposit API.

Crossref's real test system needs credentials that live outside this
repository, and it answers differently on every run.  For capturing the
manual we need the success path to look the same every time, so this serves
the two endpoints ``CrossrefAgency`` talks to and nothing else:

* ``POST /servlet/deposit`` -- the multipart ``doMDUpload`` submission.
  Crossref answers with an HTML page whose text contains "SUCCESS"; the agency
  only looks for that word, so that is what we return.
* ``GET /servlet/submissionDownload`` -- the submission log, as a
  ``doi_batch_diagnostic`` document.

The deposited XML is written to ``deposits/`` so the manual can quote the
document WEKO actually built rather than a hand-written sample.

Set ``CROSSREF_STUB_PENDING_POLLS=n`` to answer the first n polls of a batch
with ``status="unknown_submission"`` -- Crossref's "not judged yet" answer --
before reporting success.  The default, 0, succeeds on the first poll.

Standard library only: the container is a plain ``python:3.11-slim``.
"""

import cgi
import os
import re
import xml.sax.saxutils as saxutils
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get('CROSSREF_STUB_PORT', '8000'))
PENDING_POLLS = int(os.environ.get('CROSSREF_STUB_PENDING_POLLS', '0'))
DEPOSIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'deposits')

# doi_batch_id -> the DOIs found in the deposited document.
DEPOSITS = {}
# doi_batch_id -> how many times the submission log has been fetched.
POLL_COUNT = defaultdict(int)

DOI_IN_XML = re.compile(r'<doi>\s*([^<\s]+)\s*</doi>')

DEPOSIT_OK = (
    '<html><head><title>SUCCESS</title></head>'
    '<body><h2>SUCCESS</h2>'
    '<p>Your batch submission was successfully received.</p>'
    '</body></html>'
)

# Crossref's answer for a submission it has not started processing yet.  The
# agency treats this as "still pending", not as an error.
PENDING_LOG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<doi_batch_diagnostic status="unknown_submission" sp="stub">\n'
    '  <submission_id>{submission_id}</submission_id>\n'
    '  <batch_id>{batch_id}</batch_id>\n'
    '</doi_batch_diagnostic>\n'
)

SUCCESS_LOG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<doi_batch_diagnostic status="completed" sp="stub">\n'
    '  <submission_id>{submission_id}</submission_id>\n'
    '  <batch_id>{batch_id}</batch_id>\n'
    '  <record_diagnostic status="Success">\n'
    '    <doi>{doi}</doi>\n'
    '    <msg>Successfully added</msg>\n'
    '  </record_diagnostic>\n'
    '  <batch_data>\n'
    '    <record_count>1</record_count>\n'
    '    <success_count>1</success_count>\n'
    '    <warning_count>0</warning_count>\n'
    '    <failure_count>0</failure_count>\n'
    '  </batch_data>\n'
    '</doi_batch_diagnostic>\n'
)


def submission_id(batch_id):
    """Derive a stable numeric submission id from the batch id."""
    return str(abs(hash(batch_id)) % 10 ** 10)


class CrossrefStubHandler(BaseHTTPRequestHandler):
    """Serve the two endpoints CrossrefAgency uses."""

    server_version = 'CrossrefStub/1.0'

    def log_message(self, fmt, *args):
        """Log to stdout so `docker compose logs` shows the exchange."""
        print('[crossref-stub] {0}'.format(fmt % args), flush=True)

    def _respond(self, status, body, content_type):
        payload = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        """Accept a doMDUpload deposit."""
        if urlparse(self.path).path != '/servlet/deposit':
            self._respond(404, 'not found', 'text/plain')
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type']})

        if 'fname' not in form:
            self._respond(400, 'FAILURE: no fname part', 'text/plain')
            return

        file_name = form['fname'].filename or 'deposit.xml'
        xml = form['fname'].file.read().decode('utf-8')
        batch_id = os.path.splitext(os.path.basename(file_name))[0]

        dois = DOI_IN_XML.findall(xml)
        DEPOSITS[batch_id] = dois
        POLL_COUNT[batch_id] = 0

        os.makedirs(DEPOSIT_DIR, exist_ok=True)
        with open(os.path.join(DEPOSIT_DIR, '{0}.xml'.format(batch_id)),
                  'w', encoding='utf-8') as handle:
            handle.write(xml)

        self.log_message('deposit %s login_id=%s dois=%s',
                         batch_id, form.getvalue('login_id'), dois)
        self._respond(200, DEPOSIT_OK, 'text/html')

    def do_GET(self):
        """Answer a submission log poll."""
        parsed = urlparse(self.path)
        if parsed.path != '/servlet/submissionDownload':
            self._respond(404, 'not found', 'text/plain')
            return

        params = parse_qs(parsed.query)
        batch_id = (params.get('doi_batch_id') or [''])[0]
        POLL_COUNT[batch_id] += 1
        attempt = POLL_COUNT[batch_id]

        if attempt <= PENDING_POLLS:
            self.log_message('poll %s -> unknown_submission (%d/%d)',
                             batch_id, attempt, PENDING_POLLS)
            self._respond(200,
                          PENDING_LOG.format(
                              submission_id=submission_id(batch_id),
                              batch_id=saxutils.escape(batch_id)),
                          'text/xml')
            return

        dois = DEPOSITS.get(batch_id) or ['10.0000/unknown']
        self.log_message('poll %s -> completed', batch_id)
        self._respond(200,
                      SUCCESS_LOG.format(
                          submission_id=submission_id(batch_id),
                          batch_id=saxutils.escape(batch_id),
                          doi=saxutils.escape(dois[0])),
                      'text/xml')


def main():
    """Run the stub until the container stops."""
    server = ThreadingHTTPServer(('0.0.0.0', PORT), CrossrefStubHandler)
    print('[crossref-stub] listening on 0.0.0.0:{0} '
          '(pending polls: {1})'.format(PORT, PENDING_POLLS), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
