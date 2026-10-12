from rest_framework import serializers
from src.api_core.serializers import ResultSerializer


class CredentialsSerializer(serializers.Serializer):
    email = serializers.CharField(allow_null=True)
    pwd = serializers.CharField(allow_null=True)


class SignInSerializer(CredentialsSerializer):
    ...


class SignUpSerializer(CredentialsSerializer):
    ...

class DemandAcceptedSerializer(serializers.Serializer):
    process_token = serializers.CharField()


class Sign2FAFeedbackSerializer(serializers.Serializer):
    process_token = serializers.CharField(allow_null=True)
    code = serializers.CharField(allow_null=True)


class SignInDataSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class SingUpResultSerializer(ResultSerializer):
    body = DemandAcceptedSerializer(source='data')

class SingUp2FAFeedbackResultSerializer(ResultSerializer):
    body = SignInDataSerializer(source='data')

class SignIn200ResultSerializer(ResultSerializer):
    body = SignInDataSerializer(source='data')

class SignIn202ResultSerializer(ResultSerializer):
    body = DemandAcceptedSerializer(source='data')
