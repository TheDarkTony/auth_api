

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from src.api_core.decorators import allow_anonymous

@allow_anonymous()
@api_view(['GET'])
def api_root(request):

    return Response(
        {
            'identities': reverse('identity-list', request=request),
            'users': reverse('user-list', request=request),
            'profile': reverse('profile-details', request=request),

            #permission-management-panel
            'app_resources': reverse('app-resource-list', request=request),
            'roles': reverse('role-list', request=request),
            'permissions': reverse('permission-list', request=request),

            #pizza
            'orders': reverse('order-list', request=request)
        }
    )
