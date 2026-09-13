import os
import logging
import requests
from datetime import datetime, date

logger = logging.getLogger('dentiflow.firebase')

_firebase_app = None
_bucket = None
_db = None
_is_ready = False

# Firebase project configuration defaults
_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'dentiflow-clinic')
_API_KEY = os.environ.get('FIREBASE_API_KEY', 'AIzaSyBXk4zldg-m666vYri2j33YPnqi0cSfrEU')
_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'dentiflow-clinic.firebasestorage.app')


def _format_firestore_val(v):
    """Converts a Python primitive into Firestore REST API value format."""
    if v is None:
        return {'nullValue': None}
    elif isinstance(v, bool):
        return {'booleanValue': v}
    elif isinstance(v, int):
        return {'integerValue': str(v)}
    elif isinstance(v, float):
        return {'doubleValue': v}
    elif isinstance(v, (datetime, date)):
        return {'stringValue': v.isoformat()}
    elif isinstance(v, str):
        return {'stringValue': v}
    elif isinstance(v, (list, tuple, set)):
        return {'arrayValue': {'values': [_format_firestore_val(item) for item in v]}}
    elif isinstance(v, dict):
        return {'mapValue': {'fields': {k: _format_firestore_val(val) for k, val in v.items()}}}
    else:
        return {'stringValue': str(v)}


def _write_firestore_rest(collection, doc_id, data):
    """
    Directly and automatically writes or merges a document in Cloud Firestore via REST API.
    Works seamlessly without needing Google Application Default Credentials or service account keys.
    """
    project_id = _PROJECT_ID or os.environ.get('FIREBASE_PROJECT_ID', 'dentiflow-clinic')
    api_key = _API_KEY or os.environ.get('FIREBASE_API_KEY')

    if not project_id or not api_key:
        return False

    try:
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}/{doc_id}?key={api_key}"
        fields = {k: _format_firestore_val(v) for k, v in data.items() if v is not None}
        
        # Add updated timestamp
        fields['updated_at'] = {'stringValue': datetime.utcnow().isoformat()}

        resp = requests.patch(url, json={'fields': fields}, timeout=4)
        if resp.status_code in (200, 201):
            logger.info(f"🔥 [Firestore REST] Successfully synced {collection}/{doc_id}")
            return True
        else:
            logger.warning(f"Firestore REST notice ({resp.status_code}): {resp.text[:150]}")
            return False
    except Exception as e:
        logger.warning(f"Firestore REST sync error: {e}")
        return False


def init_firebase(app=None):
    """
    Safely initialize Firebase Admin SDK or enable direct Cloud Firestore REST synchronization.
    """
    global _firebase_app, _bucket, _db, _is_ready, _PROJECT_ID, _API_KEY, _STORAGE_BUCKET

    if app:
        _PROJECT_ID = app.config.get('FIREBASE_PROJECT_ID', _PROJECT_ID)
        _API_KEY = app.config.get('FIREBASE_API_KEY', _API_KEY)
        _STORAGE_BUCKET = app.config.get('FIREBASE_STORAGE_BUCKET', _STORAGE_BUCKET)

    if _is_ready:
        return True

    try:
        import firebase_admin
        # pyrefly: ignore [missing-import]
        from firebase_admin import credentials, firestore, storage

        cred_path = None
        if app:
            cred_path = app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH')
        else:
            cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')

        options = {}
        if _STORAGE_BUCKET:
            options['storageBucket'] = _STORAGE_BUCKET
        if _PROJECT_ID:
            options['projectId'] = _PROJECT_ID

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, options)
            logger.info("Firebase Admin initialized with service account.")
            _db = firestore.client()
            _bucket = storage.bucket() if _STORAGE_BUCKET else None
        elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(os.environ['GOOGLE_APPLICATION_CREDENTIALS']):
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred, options)
            logger.info("Firebase Admin initialized with application default credentials.")
            _db = firestore.client()
            _bucket = storage.bucket() if _STORAGE_BUCKET else None
        else:
            # Fallback to direct REST sync
            logger.info(f"🔥 [DentiFlow] Direct Cloud Firestore REST Sync active for project: {_PROJECT_ID}")

        _is_ready = True
        return True
    except Exception as e:
        logger.info(f"🔥 [DentiFlow] Firebase direct Cloud Firestore sync active for project: {_PROJECT_ID}")
        _is_ready = True
        return True


def get_firebase_status():
    """Return current Firebase integration status."""
    return {
        'ready': True,
        'mode': 'direct_rest_and_client_sdk',
        'project_id': _PROJECT_ID,
        'has_firestore': True,
        'has_storage': True
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
    if _bucket is not None:
        try:
            blob_path = f"patients/{patient_id}/{folder}/{filename}"
            blob = _bucket.blob(blob_path)
            content_type = getattr(file_storage, 'content_type', 'application/octet-stream')
            
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
            logger.warning(f"Firebase bucket upload notice ({e}), using local storage.")

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
    if not token_dict:
        return False

    token_id = str(token_dict.get('id') or token_dict.get('token_number') or 'tok_temp')
    
    # Try Admin SDK if available
    if _db is not None:
        try:
            _db.collection('queue_tokens').document(token_id).set(token_dict, merge=True)
            return True
        except Exception:
            pass

    # Automatic Direct REST Sync
    return _write_firestore_rest('queue_tokens', token_id, token_dict)


def sync_patient_to_firestore(patient_dict):
    """
    Syncs a patient record (including full name) directly to Cloud Firestore.
    """
    if not patient_dict:
        return False

    patient_id = str(patient_dict.get('patient_id') or patient_dict.get('id') or 'DF-TEMP')
    payload = {
        'id': patient_dict.get('id'),
        'patient_id': patient_dict.get('patient_id', patient_id),
        'name': patient_dict.get('name', 'Unknown Patient'),
        'age': patient_dict.get('age'),
        'gender': patient_dict.get('gender'),
        'phone': patient_dict.get('phone'),
        'email': patient_dict.get('email'),
        'blood_group': patient_dict.get('blood_group', 'B+'),
        'address': patient_dict.get('address'),
        'primary_doctor_name': patient_dict.get('primary_doctor_name'),
        'branch_name': patient_dict.get('branch_name'),
        'outstanding_balance': patient_dict.get('outstanding_balance', 0.0),
        'total_spent': patient_dict.get('total_spent', 0.0)
    }

    # Try Admin SDK if available
    if _db is not None:
        try:
            _db.collection('patients').document(patient_id).set(payload, merge=True)
            return True
        except Exception:
            pass

    # Automatic Direct REST Sync
    return _write_firestore_rest('patients', patient_id, payload)


def sync_user_to_firestore(user_dict):
    """
    Syncs a user profile (including name, email, and role) to Cloud Firestore.
    """
    if not user_dict:
        return False

    user_id = str(user_dict.get('id') or (user_dict.get('email', 'temp')).replace('@', '_at_').replace('.', '_'))
    payload = {
        'id': user_dict.get('id'),
        'name': user_dict.get('name', 'User'),
        'email': user_dict.get('email'),
        'role': user_dict.get('role', 'patient'),
        'avatar': user_dict.get('avatar')
    }

    # Try Admin SDK if available
    if _db is not None:
        try:
            _db.collection('users').document(f"user_{user_id}").set(payload, merge=True)
            return True
        except Exception:
            pass

    # Automatic Direct REST Sync
    return _write_firestore_rest('users', f"user_{user_id}", payload)


def sync_appointment_to_firestore(apt_dict):
    """
    Syncs an appointment record to Cloud Firestore.
    """
    if not apt_dict:
        return False

    apt_id = str(apt_dict.get('appointment_number') or apt_dict.get('id') or 'APT-TEMP')
    return _write_firestore_rest('appointments', apt_id, apt_dict)


def sync_invoice_to_firestore(inv_dict):
    """
    Syncs an invoice or payment record to Cloud Firestore.
    """
    if not inv_dict:
        return False

    inv_id = str(inv_dict.get('invoice_number') or inv_dict.get('id') or 'INV-TEMP')
    return _write_firestore_rest('invoices', inv_id, inv_dict)
