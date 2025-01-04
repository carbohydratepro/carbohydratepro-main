from rest_framework import serializers
from .models import SensorData

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['timestamp', 'temperature', 'humidity', 'illuminance']
        read_only_fields = ['timestamp']  # タイムスタンプは読み取り専用