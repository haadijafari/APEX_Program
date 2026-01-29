import os

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseNotModified
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def emoji_data_view(request):
    """
    Manually serves the emoji data.json with a strong ETag header.
    This satisfies the emoji-picker-element efficiency check.
    """
    # Build path to the file on disk
    file_path = settings.BASE_DIR / "static" / "vendor" / "emoji-picker" / "data.json"

    if not os.path.exists(file_path):
        raise Http404("Emoji database not found")

    # Generate a lightweight ETag based on modification time and file size
    stats = os.stat(file_path)
    etag = f'"{stats.st_mtime}-{stats.st_size}"'

    # 1. Check if the browser already has this version (Efficiency Check)
    if request.headers.get("If-None-Match") == etag:
        return HttpResponseNotModified()

    # 2. If not, read and serve the file
    try:
        with open(file_path, "rb") as f:
            content = f.read()
    except IOError:
        raise Http404("Error reading emoji database")

    response = HttpResponse(content, content_type="application/json")
    response["ETag"] = etag
    # Cache heavily (1 year) since we have a working ETag system now
    response["Cache-Control"] = "public, max-age=31536000"
    return response
