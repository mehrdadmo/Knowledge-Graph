from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class MultipleFileUploadSerializer(serializers.Serializer):
    # files = serializers.FileField()
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        allow_empty=False
    )

    def validate_files(self, value):
        if len(value) > 10:  # Limit to 10 files max
            raise serializers.ValidationError("Cannot upload more than 10 files at once")

        # Validate each file size (max 50MB each)
        max_size = 50 * 1024 * 1024  # 50MB
        for file in value:
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"File {file.name} is too large. Maximum size is 50MB"
                )

        return value