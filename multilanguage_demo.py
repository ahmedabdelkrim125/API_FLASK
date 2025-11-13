"""
Multi-language Support Demo
This script demonstrates how the multi-language support works in our Flask API
"""

from translations import translate
from utils import create_response, create_error_response

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
    
    # Test response creation
    print("\nResponse Creation:")
    print("-" * 20)
    success_response = create_response('booking_created_successfully', {
        'booking_id': 123,
        'field_name': 'Stadium A'
    })
    print(f"Success response: {success_response}")
    
    error_response = create_error_response('field_not_found', 'Field ID: 456')
    print(f"Error response: {error_response}")

def demo_unsupported_language():
    """Demonstrate behavior with unsupported language"""
    print("\nUnsupported Language Handling:")
    print("-" * 30)
    # Should fall back to English
    message = translate('user_logged_in_successfully', 'fr')
    print(f"French (unsupported) -> English: {message}")

def show_available_translations():
    """Show all available translations"""
    from translations import translations
    
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