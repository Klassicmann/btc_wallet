# wallet/api/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from django.contrib.auth.models import User
from django.conf import settings

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
            
        try:
            # Remove 'Bearer ' from token
            id_token = auth_header.split(' ')[1]
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)
            
            # Get or create user
            email = decoded_token.get('email')
            if not email:
                raise AuthenticationFailed('No email in Firebase token')
                
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,  # Or decoded_token.get('name', email)
                }
            )
            
            return (user, None)
        except Exception as e:
            raise AuthenticationFailed(str(e))

    def authenticate_header(self, request):
        return 'Bearer'