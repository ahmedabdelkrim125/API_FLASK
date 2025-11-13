from flask import request
from translations import translate

def get_language():
    """Get language from request headers or default to English"""
    lang = request.headers.get('Accept-Language', 'en')
    # Extract primary language (e.g., 'en-US' -> 'en')
    if '-' in lang:
        lang = lang.split('-')[0]
    # Support only 'en' and 'ar' for now
    if lang not in ['en', 'ar']:
        lang = 'en'
    return lang

def t(key):
    """Translate a key to the current language"""
    lang = get_language()
    return translate(key, lang)

def create_response(message_key, data=None, status_code=200):
    """Create a standardized response with translation"""
    lang = get_language()
    message = translate(message_key, lang)
    
    response_data = {'message': message}
    if data is not None:
        response_data.update(data)
    
    return response_data, status_code

def create_error_response(message_key, error=None, status_code=400):
    """Create a standardized error response with translation"""
    lang = get_language()
    message = translate(message_key, lang)
    
    response_data = {'message': message}
    if error is not None:
        response_data['error'] = str(error)
    
    return response_data, status_code