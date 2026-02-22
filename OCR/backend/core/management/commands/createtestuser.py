# your_app/management/commands/createtestuser.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test user with username "test" and password "123123"'

    def handle(self, *args, **options):
        # Check if user already exists
        username = 'test'
        password = '123123'
        email = 'test@example.com'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))

            # If you want to update the password if user exists:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated password for existing user "{username}"'))
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created user "{username}"'))

        # Generate tokens similar to your RegisterView
        refresh = RefreshToken.for_user(user)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("User created successfully!"))
        self.stdout.write(f"Username: {username}")
        self.stdout.write(f"Password: {password}")
        self.stdout.write(f"Email: {email}")
        self.stdout.write("\nTokens generated:")
        self.stdout.write(f"Refresh Token: {str(refresh)}")
        self.stdout.write(f"Access Token: {str(refresh.access_token)}")
        self.stdout.write("=" * 50)