import jwt
import datetime
import time
from django.conf import settings
from functools import wraps
from rest_framework.response import Response
from .db import logs_col

def generate_token(user_id, is_admin):
    payload = {
        'user_id': str(user_id),
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def token_required(f):
    @wraps(f)
    def wrapper(self,request, *args, **kwargs):
        
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header:
            return Response({"error": "Authorization header is missing"}, status=401)
        
        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return Response({"error": "Invalid format. Use: Bearer <token>"}, status=401)
            
            token = parts[1]
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            request.user_info = decoded_data
            
                
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token has expired"}, status=401)
        except Exception as e:
            return Response({"error": f"Invalid token: {str(e)}"}, status=401)
            
        return f(self, request, *args, **kwargs)
    return wrapper

def log_api_request(endpoint, params, user_id, start_time):
    execution_time = time.time() - start_time
    logs_col.insert_one({
        "endpoint": endpoint,
        "params": params,
        "user_id": user_id,
        "execution_time": execution_time,
        "timestamp": datetime.datetime.utcnow()
    })