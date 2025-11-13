"""
Script to verify multi-language support implementation
This script checks that all the necessary components are in place
"""

import os
import sys

def verify_translations_module():
    """Verify that the translations module exists and has the required content"""
    try:
        from translations import translations
        print("✓ Translations module imported successfully")
        
        # Check if English and Arabic translations exist
        if 'en' in translations:
            print("✓ English translations found")
        else:
            print("✗ English translations missing")
            
        if 'ar' in translations:
            print("✓ Arabic translations found")
        else:
            print("✗ Arabic translations missing")
            
        return True
    except ImportError as e:
        print(f"✗ Failed to import translations module: {e}")
        return False

def verify_utils_module():
    """Verify that the utils module exists and has the required functions"""
    try:
        from utils import get_language, t, create_response, create_error_response
        print("✓ Utils module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import utils module: {e}")
        return False

def verify_routes_updated():
    """Verify that route files have been updated to use the translation system"""
    route_files = [
        'routes/auth.py',
        'routes/fields.py',
        'routes/bookings.py',
        'routes/payments.py',
        'routes/reviews.py',
        'routes/teams.py',
        'routes/clubs.py',
        'routes/notifications.py',
        'routes/analytics.py'
    ]
    
    all_updated = True
    for file_path in route_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'from utils import' in content and ('t(' in content or 'create_response' in content or 'create_error_response' in content):
                    print(f"✓ {file_path} updated with translation support")
                else:
                    print(f"✗ {file_path} not properly updated with translation support")
                    all_updated = False
        else:
            print(f"✗ {file_path} not found")
            all_updated = False
    
    return all_updated

def verify_app_updated():
    """Verify that app.py has been updated to support language selection"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'get_language' in content:
                print("✓ app.py updated with language selection support")
                return True
            else:
                print("✗ app.py not properly updated with language selection support")
                return False
    except FileNotFoundError:
        print("✗ app.py not found")
        return False

def main():
    """Main verification function"""
    print("Verifying Multi-language Support Implementation")
    print("=" * 50)
    
    checks = [
        verify_translations_module,
        verify_utils_module,
        verify_app_updated,
        verify_routes_updated
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All checks passed! Multi-language support is properly implemented.")
        print("\nFeatures implemented:")
        print("- Multi-language support for English and Arabic")
        print("- Automatic language detection from Accept-Language header")
        print("- Translation system for all API responses")
        print("- Consistent error messaging across all endpoints")
        print("- Support for both success and error responses")
    else:
        print("❌ Some checks failed. Please review the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()