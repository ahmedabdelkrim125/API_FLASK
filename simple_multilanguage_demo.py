"""
Simple Multi-language Support Demo
This script demonstrates how the multi-language support works without requiring Flask
"""

# Import the translations module directly
from translations import translations

def translate(key, language='en'):
    """Translate a key to a specific language"""
    # Fallback to English if language not supported
    lang_translations = translations.get(language, translations['en'])
    # Fallback to key if translation not found
    return lang_translations.get(key, key)

def demo_translations():
    """Demonstrate translation functionality"""
    print("Multi-language Support Demo")
    print("=" * 40)
    
    # Test English translations
    print("\nEnglish Translations:")
    print("-" * 20)
    print(f"User created: {translate('user_created_successfully', 'en')}")
    print(f"Invalid credentials: {translate('invalid_email_or_password', 'en')}")
    print(f"Field not found: {translate('field_not_found', 'en')}")
    print(f"Booking created: {translate('booking_created_successfully', 'en')}")
    
    # Test Arabic translations
    print("\nArabic Translations:")
    print("-" * 20)
    print(f"User created: {translate('user_created_successfully', 'ar')}")
    print(f"Invalid credentials: {translate('invalid_email_or_password', 'ar')}")
    print(f"Field not found: {translate('field_not_found', 'ar')}")
    print(f"Booking created: {translate('booking_created_successfully', 'ar')}")
    
    # Test response creation concept
    print("\nResponse Creation Concept:")
    print("-" * 25)
    def create_response(message_key, data=None, status_code=200, language='en'):
        """Create a standardized response with translation"""
        message = translate(message_key, language)
        response_data = {'message': message}
        if data is not None:
            response_data.update(data)
        return response_data, status_code
    
    success_response = create_response('booking_created_successfully', {
        'booking_id': 123,
        'field_name': 'Stadium A'
    }, language='en')
    print(f"Success response (English): {success_response}")
    
    success_response_ar = create_response('booking_created_successfully', {
        'booking_id': 123,
        'field_name': 'Stadium A'
    }, language='ar')
    print(f"Success response (Arabic): {success_response_ar}")
    
    error_response = create_response('field_not_found', {
        'error': 'Field ID: 456'
    }, status_code=404, language='en')
    print(f"Error response (English): {error_response}")

def demo_unsupported_language():
    """Demonstrate behavior with unsupported language"""
    print("\nUnsupported Language Handling:")
    print("-" * 30)
    # Should fall back to English
    message = translate('user_logged_in_successfully', 'fr')
    print(f"French (unsupported) -> English: {message}")

def show_available_translations():
    """Show all available translations"""
    print("\nAvailable Languages:")
    print("-" * 20)
    for lang_code in translations.keys():
        print(f"- {lang_code}")
        
    print("\nTranslation Keys (English):")
    print("-" * 25)
    for key in translations['en'].keys():
        print(f"- {key}")

if __name__ == "__main__":
    demo_translations()
    demo_unsupported_language()
    show_available_translations()
    
    print("\n" + "=" * 40)
    print("Demo completed successfully!")
    print("\nIn your Flask API, the language is automatically")
    print("detected from the Accept-Language HTTP header.")
    print("\nExample usage in routes:")
    print("  - English request: Accept-Language: en")
    print("  - Arabic request: Accept-Language: ar")
    print("  - Unsupported language falls back to English")