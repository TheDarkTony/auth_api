from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response

from core_contracts.handler import Response as AppResponse


class Offer:

    def __init__(self, serializer: serializers.BaseSerializer, result: AppResponse) -> None:
        self.serializer = serializer
        self.result = result

    @property
    def offer(self):

        match self.result.status:
            case 200:
                status_code = status.HTTP_200_OK
            case 201:
                status_code = status.HTTP_201_CREATED
            case 202:
                status_code = status.HTTP_202_ACCEPTED
            case 204:
                status_code = status.HTTP_204_NO_CONTENT
            case 400:
                status_code = status.HTTP_400_BAD_REQUEST
            case 401:
                status_code = status.HTTP_401_UNAUTHORIZED
            case 403:
                status_code = status.HTTP_403_FORBIDDEN
            case 404:
                status_code = status.HTTP_404_NOT_FOUND
            case 410:
                status_code = status.HTTP_410_GONE
            case _:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(self.serializer.data, status=status_code)