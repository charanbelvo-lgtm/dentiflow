# Firebase Setup & Quickstart Guide for DentiFlow

DentiFlow includes built-in, safe support for **Firebase Cloud Storage** (for dental X-rays, CBCT scans, and consent PDFs) and **Cloud Firestore** (for real-time waiting room token sync).

---

## 1. Create a Firebase Project (2 Minutes)

1. Open the [Firebase Console](https://console.firebase.google.com/) and click **Add project**.
2. Name your project (e.g. `dentiflow-clinic`).
3. Click **Continue** and finish creating the project.

---

## 2. Enable Services

### A. Cloud Firestore (Real-Time Queue & Live Sync)
1. In the Firebase console left menu, click **Firestore Database** ➔ **Create database**.
2. Choose **Start in production mode** (or test mode for local testing).
3. Select your preferred server location (e.g. `asia-south1` for Mumbai / Bengaluru).
4. Apply the security rules from `firestore.rules`.

### B. Firebase Storage (Dental Scans & Documents)
1. In the left menu, click **Storage** ➔ **Get Started**.
2. Accept the default bucket rules.
3. Apply the security rules from `storage.rules`.

### C. Web App Registration
1. In Project Settings (⚙️ icon) ➔ **General** ➔ **Your apps**, click the **Web icon (`</>`)**.
2. Register the app (e.g. `DentiFlow Web`).
3. Copy the `firebaseConfig` credentials object.

---

## 3. Add Keys to DentiFlow

Add your copied keys to your `.env` file or environment variables:

```env
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456
```

*(Optional for Backend Admin operations)*:
Download your Admin Service Account JSON from **Project Settings ➔ Service accounts ➔ Generate new private key**, save it as `firebase-service-account.json` in the root directory.

---

## 4. Run DentiFlow

Start your server normally:
```bash
python app.py
```

DentiFlow will automatically detect the Firebase keys:
- **Cloud Storage** will be used automatically for all dental radiographs and document uploads.
- **Firestore** will automatically synchronize waiting room tokens in real time across reception and operatory screens.
- If keys are missing, DentiFlow will automatically and safely fall back to local disk storage and REST polling without any errors!
