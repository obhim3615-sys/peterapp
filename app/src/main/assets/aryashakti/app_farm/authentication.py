from rest_framework.authentication import TokenAuthentication
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import get_authorization_header
from django.utils.translation import gettext_lazy as _

from app_farm.models import AuthenticationToken

class CustomTokenAuthentication(TokenAuthentication):
    model = AuthenticationToken

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode() :
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token, request.path + '##' + request.method.lower())

    def authenticate_credentials(self, key, path):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active or  token.user.is_deleted:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))
        
        #Check permission for API
        # try:
        #     token.user.user_role.permissions.get(api=path)
        # except:
        #     raise exceptions.PermissionDenied(_('Not authorized.'))

        return (token.user, token)
    