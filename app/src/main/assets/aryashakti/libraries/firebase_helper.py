from .push_notification import FirebaseHelper
firebase_helper_instance = None

def get_firebase_helper():
    global firebase_helper_instance
    if firebase_helper_instance is None:
        print("Initializing Firebase app once...")
        firebase_helper_instance = FirebaseHelper(use_adc=True)
    return firebase_helper_instance