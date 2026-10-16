from rest_framework import serializers


class KeyRequestSerializer(serializers.Serializer):
    consumer_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()


class KeyResponseSerializer(serializers.Serializer):
    api_key = serializers.CharField()
    consumer_name = serializers.CharField()
    email = serializers.EmailField()
    message = serializers.CharField()
