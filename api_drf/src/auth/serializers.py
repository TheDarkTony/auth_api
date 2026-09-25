from rest_framework import serializers
from src.api_core.serializers import ResultSerializer
from src.auth.wrappers import SignUpDemand, Sign2FAFeedbackDemand, SignInDemand


class CredentialsSerializer(serializers.Serializer):
    email = serializers.CharField(allow_null=True)
    pwd = serializers.CharField(allow_null=True)


class SignInSerializer(CredentialsSerializer):

    def create(self, validated_data) -> SignInDemand:
                return SignInDemand(**validated_data)
    
    @property
    def demand(self) -> SignInDemand:
        self.is_valid()
        return self.create(self.validated_data)


class SignUpSerializer(CredentialsSerializer):

    def create(self, validated_data) -> SignUpDemand:
            return SignUpDemand(**validated_data)

    @property
    def demand(self) -> SignUpDemand:
        self.is_valid()
        return self.create(self.validated_data)


class DemandAcceptedSerializer(serializers.Serializer):
     process_token = serializers.CharField()


class Sign2FAFeedbackSerializer(serializers.Serializer):
    process_token = serializers.CharField(allow_null=True)
    code = serializers.CharField(allow_null=True)

    def create(self, validated_data) -> Sign2FAFeedbackDemand:
            return Sign2FAFeedbackDemand(**validated_data)

    @property
    def demand(self) -> Sign2FAFeedbackDemand:
        self.is_valid()
        return self.create(self.validated_data)


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
