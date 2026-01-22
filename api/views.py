import bcrypt
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from bson import ObjectId
from .db import users_col, trains_col, bookings_col
from .utils import generate_token, token_required, log_api_request

# --- User Auth ---
class RegisterView(APIView):
    def post(self, request):
        data = request.data
        hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        user = {"name": data['name'], "email": data['email'], "password": hashed_pw, "is_admin": data.get('is_admin', False)}
        user_id = users_col.insert_one(user).inserted_id
        return Response({"message": "User registered", "token": generate_token(user_id, user['is_admin'])})

class LoginView(APIView):
    def post(self, request):
        user = users_col.find_one({"email": request.data['email']})
        if user and bcrypt.checkpw(request.data['password'].encode('utf-8'), user['password']):
            return Response({"token": generate_token(user['_id'], user['is_admin'])})
        return Response({"error": "Invalid credentials"}, status=401)

# --- Train APIs ---
class TrainView(APIView):
    def get(self, request): # Search Trains
        start_time = time.time()
        src, dest = request.query_params.get('source'), request.query_params.get('destination')
        trains = list(trains_col.find({"source": src, "destination": dest}, {"_id": 1, "name": 1, "available_seats": 1}))
        for t in trains: t['_id'] = str(t['_id']) # Convert ObjectId to string
        
        log_api_request("/api/trains/search/", request.query_params.dict(), "guest", start_time)
        return Response(trains)

    @token_required
    def post(self, request): # Admin only: Add Train
        # নিরাপদভাবে ইউজার ডাটা নেওয়া
        user_info = getattr(request, 'user_info', None)
        
        if not user_info or not user_info.get('is_admin'): 
            return Response({"error": "Admin only access required"}, status=403)
            
        trains_col.insert_one(request.data)
        return Response({"message": "Train added successfully"})

# --- Booking APIs ---
class BookingView(APIView):
    @token_required
    def post(self, request):
        train = trains_col.find_one({"_id": ObjectId(request.data['train_id'])})
        if train and train['available_seats'] > 0:
            trains_col.update_one({"_id": train['_id']}, {"$inc": {"available_seats": -1}})
            bookings_col.insert_one({
                "user_id": request.user_info['user_id'],
                "train_id": request.data['train_id'],
                "status": "Confirmed"
            })
            return Response({"message": "Booking successful!"})
        return Response({"error": "No seats available"}, status=400)

# --- Analytics ---
from .db import logs_col
class AnalyticsView(APIView):
    def get(self, request):
        pipeline = [
            {"$group": {"_id": {"source": "$params.source", "dest": "$params.destination"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 5}
        ]
        return Response(list(logs_col.aggregate(pipeline)))

class MyBookingsView(APIView):
    @token_required
    def get(self, request):
        user_id = request.user_info['user_id']
        my_bookings = list(bookings_col.find({"user_id": user_id}))
        
        for booking in my_bookings:
            booking['_id'] = str(booking['_id'])
            train = trains_col.find_one({"_id": ObjectId(booking['train_id'])}, {"_id": 0})
            booking['train_details'] = train
            
        return Response(my_bookings)