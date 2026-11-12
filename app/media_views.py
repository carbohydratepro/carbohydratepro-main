from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers

from auth_app.models import AccountMembership
from auth_app.services import get_related_memberships

from .cooking.models import CookingDish, CookingStep


def _is_authorized_media(request: HttpRequest, file_path: str) -> bool:
    if file_path.startswith('account_avatars/'):
        membership = (
            AccountMembership.objects
            .filter(user=request.user)
            .select_related('group')
            .first()
        )
        allowed_user_ids = {request.user.pk}
        if membership is not None:
            allowed_user_ids.update(
                item.user_id for item in get_related_memberships(membership.group)
            )
        return get_user_model().objects.filter(
            pk__in=allowed_user_ids,
            avatar=file_path,
        ).exists()

    if not file_path.startswith('cooking/'):
        return False

    dish_photo = Q(photo_1=file_path) | Q(photo_2=file_path) | Q(photo_3=file_path)
    dish_photo |= Q(photo_4=file_path) | Q(photo_5=file_path)
    if CookingDish.objects.filter(dish_photo, user=request.user).exists():
        return True
    return CookingStep.objects.filter(
        Q(photo_1=file_path) | Q(photo_2=file_path),
        dish__user=request.user,
    ).exists()


@login_required
def protected_media(request: HttpRequest, file_path: str) -> HttpResponse:
    """所有者（または連携済みアカウント）だけにアップロードを配信する。"""
    if not getattr(request.user, 'is_email_verified', False):
        raise Http404
    normalized = PurePosixPath(file_path)
    if normalized.is_absolute() or '..' in normalized.parts or str(normalized) != file_path:
        raise Http404
    if not _is_authorized_media(request, file_path) or not default_storage.exists(file_path):
        raise Http404

    content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    if settings.DEBUG:
        response = FileResponse(default_storage.open(file_path, 'rb'), content_type=content_type)
    else:
        response = HttpResponse(content_type=content_type)
        response['X-Accel-Redirect'] = f'/_protected_media/{quote(file_path, safe="/")}'
    response['Cache-Control'] = 'private, no-store'
    patch_vary_headers(response, ('Cookie',))
    return response
