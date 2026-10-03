
from recordActivity.models import ExternalClient,APICalledAnalytic

from rest_framework.permissions import BasePermission

class HasValidTokenPermission(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            return False

        try:
            client = ExternalClient.objects.get(token=token)
        except ExternalClient.DoesNotExist:
            return False

        if client.available_count <= 0 and client.available_count!=-999:
            return False

        # Deduct one credit for a successful API call
        # client.available_count -= 1
        # client.save()
       

        request.client = client

        return True