import firebase_admin
from firebase_admin import credentials, db, messaging
from django.conf import settings
import os
import concurrent.futures
import time

class FirebaseHelper:
    

    def __init__(self, use_adc=False):
        """
        Initializes Firebase using either a service account key or Application Default Credentials (ADC).
        """
        # Check if Firebase app already exists
        try:
            self.app = firebase_admin.get_app()
            print(f"Firebase App Name: {self.app.name}")
            print(f"Firebase Project ID: {self.app.project_id}")  # Should print 'arya-shakti-3a019'
        except ValueError:
            if use_adc:
                self.initialize_with_adc()
            else:
                self.initialize_with_key()

    def initialize_with_key(self):
        """
        Initializes Firebase using a service account key file.
        """
        firebase_admin_sdk_path = settings.BASE_DIR + settings.STATIC_URL + 'certificates/firebase_cred.json'
        cred = credentials.Certificate(firebase_admin_sdk_path)
        self.app = firebase_admin.initialize_app(cred, {"databaseURL": settings.FIREBASE_DATABASE_URL,"projectId":"arya-shakti-3a019","api_url": "https://fcm.googleapis.com/v1/projects/arya-shakti-3a019/messages:send"})

    def initialize_with_adc(self):
        """
        Initializes Firebase using Application Default Credentials (ADC).
        This method requires the GOOGLE_APPLICATION_CREDENTIALS environment variable to be set.
        """
        self.app = firebase_admin.initialize_app(options={"databaseURL": settings.FIREBASE_DATABASE_URL,"projectId":"arya-shakti-3a019"})
        print(f"Firebase App Name: {self.app.name}")
        print(f"Firebase Project ID: {self.app.project_id}")


    def validate_fcm_token(self,fcm_token):
        """Function to validate an FCM token by sending a dry-run push notification."""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="FCM Token Validation",
                    body="This is a test message.",
                ),
                token=fcm_token,
            )

            # Send the message in dry-run mode (does not actually send)
            response = messaging.send(message, dry_run=True)
            print(f"Valid token: {response}")
            return {"valid": True, "message_id": response}

        except messaging.UnregisteredError:
            return {"valid": False, "error": "Invalid FCM token (UnregisteredError)"}
        
        except messaging.SenderIdMismatchError:
            return {"valid": False, "error": "Token does not match the project (MismatchSenderId)"}

        except messaging.InvalidArgumentError as e:
            return {"valid": False, "error": f"Invalid token format: {str(e)}"}

        except Exception as e:
            return {"valid": False, "error": f"Unknown error: {str(e)}"}
        
    def send_single_notification(self, token, title, message, data=None):
        """Send one FCM message synchronously. Safe to call from worker threads."""
        try:
            msg = messaging.Message(
                notification=messaging.Notification(title=title, body=message),
                token=token,
                data=data or {}
            )
            response = messaging.send(msg)
            return {"success": True, "message_id": response, "token": token}
        except messaging.UnregisteredError:
            return {"success": False, "error": "UnregisteredError", "token": token, "token_invalid": True}
        except messaging.SenderIdMismatchError:
            return {"success": False, "error": "SenderIdMismatchError", "token": token, "token_invalid": True}
        except Exception as e:
            return {"success": False, "error": str(e), "token": token}
        
    # ----------------- Updated version -----------------
    def send_push_notification(self, token_data, title, message, sound="default", data={}, delay_between=0):
        """
        Sends push notifications one by one (instead of multicast) using threading.
        delay_between = optional delay (in seconds) between notifications.
        """
        if not token_data:
            return {'success': False, 'error': 'No tokens provided'}

        results = []

        # Use ThreadPoolExecutor to send notifications in parallel safely
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for token in token_data:
                # Schedule the notification
                futures.append(executor.submit(self.send_single_notification, token, title, message, data))
                
                # Optional delay (throttling)
                if delay_between > 0:
                    time.sleep(delay_between)

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        return {
            'success': True,
            'count': len(results),
            'results': results
        }


    def send_push_notification_new(self, token_data, title, message, sound="default", data={}):
        """
        Sends notifications in batches of 500 using Firebase multicast.
        """
        if not token_data:
            return {"success": False, "error": "No tokens provided"}

        results = []
        batch_size = 500

        for i in range(0, len(token_data), batch_size):
            batch = token_data[i:i + batch_size]
            multicast_message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=message),
                data=data,
                tokens=batch,
            )
            response = messaging.send_multicast(multicast_message)
            results.append({
                "batch": i // batch_size + 1,
                "success_count": response.success_count,
                "failure_count": response.failure_count
            })

        return {"success": True, "batches": len(results), "results": results}







    def update_firebase_database(self, user_id, msg):
        """
        Sends real-time updates to Firebase Realtime Database.
        """
        user_data = db.reference(settings.FIREBASE_DATABASE_NAME + "users/u_" + user_id)
        if user_data is None:
            users = db.reference(settings.FIREBASE_DATABASE_NAME + "users")
            users.set("u_" + user_id)
        else:
            user_data.update({
                'message': msg
            })
