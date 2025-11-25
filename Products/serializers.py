from rest_framework import serializers

class PriceRecordUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError("Only XLSX files are allowed.")
        return value
