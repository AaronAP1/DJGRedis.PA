from rest_framework import serializers


class ImportPreviewRowSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()
    codigo = serializers.CharField(required=False, allow_blank=True)
    estado = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["valid", "invalid"])  # type: ignore
    errors = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class ImportPreviewResponseSerializer(serializers.Serializer):
    rows = ImportPreviewRowSerializer(many=True)
    valid_count = serializers.IntegerField()
    invalid_count = serializers.IntegerField()


class ImportConfirmResponseSerializer(serializers.Serializer):
    created_count = serializers.IntegerField()
    rows = ImportPreviewRowSerializer(many=True)
    valid_count = serializers.IntegerField()
    invalid_count = serializers.IntegerField()
