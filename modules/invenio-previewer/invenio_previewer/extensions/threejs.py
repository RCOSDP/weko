from __future__ import absolute_import, print_function

from flask import render_template

from ..proxies import current_previewer

previewable_extensions = ['obj']


def can_preview(file):
    """Check if file can be previewed."""
    return file.has_extensions('.obj')


def preview(file):
    """Preview file."""
    return render_template(
        'invenio_previewer/threejs.html',
        file=file,
        js_bundles=[
            'previewer_threejs',
        ] + current_previewer.js_bundles,
    )

