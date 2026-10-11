from rest_framework import serializers
from rest_framework.reverse import reverse

from src.api_core.serializers import BatchSerializer, ResultSerializer


class LinkedModelSerializer(serializers.Serializer):
    def to_representation(self, instance):
        repr = super().to_representation(instance)
        rqst = self.context.get('request')
        viewname = self.context.get('viewname')
        if rqst is not None and viewname is not None:
            url = reverse(viewname, kwargs={'id':instance.id}, request=rqst)
            repr['url'] = url 
            
        return repr


class IdentityItemSerializer(LinkedModelSerializer):
    id = serializers.BigIntegerField()
    url = serializers.CharField(allow_null=True)
    fname = serializers.CharField()
    lname = serializers.CharField()


#serializing response
class IdentitySerializer(LinkedModelSerializer):
    id = serializers.BigIntegerField()
    url = serializers.CharField(allow_null=True)
    fname = serializers.CharField()
    lname = serializers.CharField()
    email = serializers.CharField()
    email_verified = serializers.BooleanField()
    created_date = serializers.DateTimeField()
    is_activated = serializers.BooleanField()


class IdentitiesBatchSerializer(BatchSerializer):
    items = IdentityItemSerializer(many=True)


class IdentityDemographicsSerializer(serializers.Serializer):
    
    fname = serializers.CharField(allow_null=True)
    lname = serializers.CharField(allow_null=True)


class UserSerializer(LinkedModelSerializer):
    id = serializers.BigIntegerField()
    url = serializers.CharField(allow_null=True)
    identity_id = serializers.BigIntegerField()
    role_id = serializers.IntegerField()
    username = serializers.CharField()
    email_2fa_enabled= serializers.BooleanField()


class EditUserSerializer(serializers.Serializer):
    email_2fa_enabled= serializers.BooleanField()


class ChangeUserPwdSerializer(serializers.Serializer):
    old_pwd = serializers.CharField(allow_null=True)
    new_pwd = serializers.CharField(allow_null=True)
    new_pwd_confirmed = serializers.CharField(allow_null=True)


class UsersBatchSerializer(BatchSerializer):
    items = UserSerializer(many=True)


class ProfileSerializer(serializers.Serializer):
    identity = IdentitySerializer()
    user = UserSerializer()

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        user_vn = self.context.get('user_vn')
        identity_vn = self.context.get('identity_vn')
        rqst = self.context.get('request')

        if identity_vn is not None and rqst is not None:
            repr['identity']['url'] = reverse(identity_vn, kwargs={'id':instance.identity.id}, request=rqst)

        if user_vn is not None and rqst is not None:
            repr['user']['url'] = reverse(user_vn, kwargs={'id':instance.user.id}, request=rqst)

        return repr


class IdentitiesResultSerializer(ResultSerializer):
    body = IdentitiesBatchSerializer(source='data')

class IdentityResultSerializer(ResultSerializer):
    body = IdentitySerializer(source='data')

class ProfileResultSerializer(ResultSerializer):
    body = ProfileSerializer(source='data')

class UsersResultSerializer(ResultSerializer):
    body = UsersBatchSerializer(source='data')

class UserResultSerializer(ResultSerializer):
    body = UserSerializer(source='data')
