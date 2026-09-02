#!/bin/bash
# Capture what only the command line and the deposit itself can show:
# the state of the DOI deposits, and the Crossref document WEKO built.
#
# Run it from the repository root after the Playwright capture, once the
# deposit has had a moment to run:
#
#   works/crossref-doi-manual/e2e/capture_cli.sh
#
# Writes works/crossref-doi-manual/cli/.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "${here}/../../.." && pwd)"
out="${here}/../cli"
compose="docker compose -f ${root}/docker-compose.yml -f ${here}/compose.e2e.yml"

mkdir -p "${out}"

echo "==> weko workflow doi list"
${compose} exec -T web bash -lc \
  'export PATH=/home/invenio/.virtualenvs/invenio/bin:$PATH; cd /code && \
   invenio workflow doi list' 2>/dev/null \
  | grep -v -i 'warning\|Deprecation' \
  | sed '/^[[:space:]]*$/d' > "${out}/doi-list.txt"
cat "${out}/doi-list.txt"

echo
echo "==> latest deposit document"
latest="$(ls -t "${here}/deposits"/*.xml 2>/dev/null | head -1 || true)"
if [ -n "${latest}" ]; then
  python3 -c "
import sys, xml.dom.minidom
xml = xml.dom.minidom.parse(sys.argv[1]).toprettyxml(indent='  ')
print('\n'.join(line for line in xml.splitlines() if line.strip()))
" "${latest}" > "${out}/deposit.xml"
  cat "${out}/deposit.xml"
else
  echo "no deposit captured yet; is the worker running?" >&2
fi
