from rest_framework import serializers
from rest_framework.reverse import reverse
from django.utils.http import urlencode


def append_query(url, args):
    if args is None or len(args) == 0:
        return url

    return f'{url}?{urlencode(args)}'

class MessageSerializer(serializers.Serializer):
    text = serializers.CharField()
    type = serializers.IntegerField()


class ResultSerializer(serializers.Serializer):
    state_code = serializers.IntegerField(allow_null=True)
    messages = MessageSerializer(many=True)


class BatchSerializer(serializers.Serializer):
    previous_batch_cursor = serializers.CharField(source='prev_cursor', allow_null=True)
    prev_batch_url = serializers.CharField(allow_null=True)
    next_batch_cursor = serializers.CharField(source='next_cursor', allow_null=True)
    next_batch_url = serializers.CharField(allow_null=True)

    def to_representation(self, instance):
        repr = super().to_representation(instance)

        rqst = self.context.get('request')
        viewname = self.context.get('list_viewname')
        if rqst is not None and viewname is not None:
            url = reverse(viewname, request=rqst)
            
            direction = rqst.query_params.get('direction')
            cursor = rqst.query_params.get('cursor')

            if len(instance.items) != 0:
                repr['next_batch_url'] = self.__query_batch(url, {'cursor':instance.next_cursor, 'direction': 'next'})
                if instance.prev_cursor is not None:
                    repr['prev_batch_url'] = self.__query_batch(url, {'cursor':instance.prev_cursor, 'direction': 'prev'})
            else:
                if direction == 'next':
                    repr['prev_batch_url'] = self.__query_batch(url, {'cursor': cursor, 'direction': 'prev', 'include_cursor': True}) 
                elif direction == 'prev':
                    repr['next_batch_url'] = self.__query_batch(url, {'cursor': cursor, 'direction': 'next', 'include_cursor': True})

        return repr

    def __query_batch(self, url, args):
        return f'{url}?{urlencode(args)}'