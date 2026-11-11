from rest_framework import serializers

HEALTH_STATUS_CHOICES = ('ok', 'not_ready')


class ErrorDetailSchemaSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    valid_values = serializers.ListField(child=serializers.CharField(), required=False)


class ErrorEnvelopeSchemaSerializer(serializers.Serializer):
    error = ErrorDetailSchemaSerializer()


class HealthChecksSchemaSerializer(serializers.Serializer):
    database = serializers.ChoiceField(choices=('connected', 'unavailable'))


class HealthResponseSchemaSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=HEALTH_STATUS_CHOICES)
    checks = HealthChecksSchemaSerializer(required=False)
    version = serializers.CharField()
