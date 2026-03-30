from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Pehle check karo ki JWT token request me hai ya nahi
            verify_jwt_in_request()
            
            # Token ke andar se saara data (claims) nikalo
            claims = get_jwt()
            
            # Check karo ki role 'Admin' hai ya nahi
            if claims.get('role') != 'Admin':
                return jsonify({"error": "Access Denied! Only Admin can perform this action."}), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper




def seller_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'Seller':
                return jsonify({"error": "Access Denied! Only Sellers can perform this action."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper





def customer_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'User':
                return jsonify({"error": "Access Denied! Only registered customers can add to cart."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper