import os
import logging
from datetime import datetime

logger = logging.getLogger('dentiflow.firebase')

_firebase_app = None
_bucket = None
_db = None
_is_ready = False

def init_firebase(app=None):
    """
    Safely initialize Firebase Admin SDK.
    Gracefully falls back if credentials or library are not present.
    """
    global _firebase_app, _bucket, _db, _is_ready

    if _is_ready:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

        cred_path = None
        storage_bucket = None
        project_id = None

        if app:
            cred_path = app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH')
            storage_bucket = app.config.get('FIREBASE_STORAGE_BUCKET')
            project_id = app.config.get('FIREBASE_PROJECT_ID')
        else:
            cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
            storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET')
            project_id = os.environ.get('FIREBASE_PROJECT_ID')

        options = {}
        if storage_bucket:
            options['storageBucket'] = storage_bucket
        if project_id:
            options['projectId'] = project_id

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, options)
            logger.info("Firebase Admin initialized with service account.")
        elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(os.environ['GOOGLE_APPLICATION_CREDENTIALS']):
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred, options)
            logger.info("Firebase Admin initialized with application default credentials.")
        elif project_id:
            # Initialize with default options for project
            _firebase_app = firebase_admin.initialize_app(options=options)
            logger.info(f"Firebase Admin initialized for project {project_id}.")
        else:
            logger.info("Firebase credentials not configured. Operating in local storage mode.")
            return False

        try:
            _db = firestore.client()
        except Exception as e:
            logger.warning(f"Firestore client init skipped: {e}")

        try:
            _bucket = storage.bucket() if storage_bucket else None
        except Exception as e:
            logger.warning(f"Storage bucket init skipped: {e}")

        _is_ready = True
        return True
    except ImportError:
        logger.info("firebase-admin package not installed. Local fallback active.")
        return False
    except Exception as e:
        logger.warning(f"Firebase init notice: {e}. Falling back to standard mode.")
        return False


def get_firebase_status():
    """Return current Firebase integration status."""
    return {
        'ready': _is_ready,
        'has_firestore': _db is not None,
        'has_storage': _bucket is not None
    }


def upload_patient_file(file_storage, patient_id, folder='documents', filename=None):
    """
    Upload a file (X-Ray scan, consent form, report) to Firebase Storage or local fallback.
    Returns the accessible URL string.
    """
    if not filename:
        safe_name = getattr(file_storage, 'filename', 'document.pdf')
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe_name}"

    # Try Firebase Cloud Storage
    if _is_ready and _bucket is not None:
        try:
            blob_path = f"patients/{patient_id}/{folder}/{filename}"
            blob = _bucket.blob(blob_path)
            content_type = getattr(file_storage, 'content_type', 'application/octet-stream')
            
            # If it's a file-like object
            if hasattr(file_storage, 'read'):
                file_storage.seek(0)
                blob.upload_from_file(file_storage, content_type=content_type)
            elif isinstance(file_storage, (bytes, bytearray)):
                blob.upload_from_string(file_storage, content_type=content_type)
            else:
                blob.upload_from_filename(str(file_storage), content_type=content_type)

            blob.make_public()
            return {
                'status': 'success',
                'storage': 'firebase',
                'url': blob.public_url,
                'path': blob_path
            }
        except Exception as e:
            logger.warning(f"Firebase upload failed ({e}), using local storage fallback.")

    # Local Storage Fallback
    local_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', str(patient_id), folder)
    os.makedirs(local_dir, exist_ok=True)
    local_file_path = os.path.join(local_dir, filename)

    if hasattr(file_storage, 'save'):
        file_storage.seek(0)
        file_storage.save(local_file_path)
    elif hasattr(file_storage, 'read'):
        file_storage.seek(0)
        with open(local_file_path, 'wb') as f:
            f.write(file_storage.read())
    elif isinstance(file_storage, (bytes, bytearray)):
        with open(local_file_path, 'wb') as f:
            f.write(file_storage)

    local_url = f"/static/uploads/{patient_id}/{folder}/{filename}"
    return {
        'status': 'success',
        'storage': 'local',
        'url': local_url,
        'path': local_file_path
    }


def sync_queue_token_to_firestore(token_dict):
    """
    Syncs a queue token event to Cloud Firestore for real-time waiting room displays.
    """
    if not _is_ready or _db is None:
        return False

    try:
        token_id = str(token_dict.get('id', 'temp'))
        doc_ref = _db.collection('queue_tokens').document(token_id)
        doc_ref.set(token_dict, merge=True)
        return True
    except Exception as e:
        logger.warning(f"Firestore queue token sync notice: {e}")
        return False
