/**
 * DentiFlow - Safe Firebase Client Integration Layer
 * Provides real-time Firestore sync and Storage uploads with non-blocking graceful fallback.
 */

class DentiFlowFirebaseClient {
  constructor() {
    this.isReady = false;
    this.initPromise = null;
    this.app = null;
    this.db = null;
    this.storage = null;
    this.auth = null;
    this.queueUnsubscribe = null;
    this.config = window.FIREBASE_CONFIG || {};
  }

  async init() {
    if (this.initPromise) return this.initPromise;

    this.initPromise = (async () => {
      // Check if valid Firebase configuration is provided
      if (!this.config || !this.config.apiKey || !this.config.projectId || this.config.apiKey.includes('YOUR_')) {
        console.log('ℹ️ [DentiFlow] Firebase unconfigured: Local SQL database & REST endpoints active.');
        return false;
      }

      try {
        // Dynamic ES Module imports from Google CDN
        const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js");
        const { getFirestore, doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
        const { getStorage } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-storage.js");
        const { getAuth } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js");

        this.app = initializeApp(this.config);
        this.db = getFirestore(this.app);
        this.storage = getStorage(this.app);
        this.auth = getAuth(this.app);
        this.isReady = true;

        // Automatically sync active user session to Firestore users collection
        if (window.CURRENT_USER && window.CURRENT_USER.email) {
          const userDocId = `user_${window.CURRENT_USER.id || window.CURRENT_USER.email.replace(/[^a-zA-Z0-9]/g, '_')}`;
          setDoc(doc(this.db, "users", userDocId), {
            id: window.CURRENT_USER.id,
            name: window.CURRENT_USER.name,
            email: window.CURRENT_USER.email,
            role: window.CURRENT_USER.role,
            last_sign_in: new Date().toISOString()
          }, { merge: true }).catch(() => {});
        }

        console.log('🔥 [DentiFlow] Firebase initialized successfully (Cloud Firestore + Storage active).');
        return true;
      } catch (err) {
        console.warn('⚠️ [DentiFlow] Firebase client initialization notice:', err);
        this.isReady = false;
        return false;
      }
    })();

    return this.initPromise;
  }

  async ensureReady() {
    if (this.isReady) return true;
    return await this.init();
  }

  /**
   * Real-Time Firestore Queue Listener
   */
  async subscribeToQueue(callback) {
    await this.ensureReady();
    if (!this.isReady || !this.db) return null;

    try {
      const { collection, onSnapshot, query, where } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      
      const q = query(
        collection(this.db, "queue_tokens"),
        where("status", "in", ["Waiting", "Serving"])
      );

      this.queueUnsubscribe = onSnapshot(q, (snapshot) => {
        const tokens = [];
        snapshot.forEach((doc) => {
          tokens.push({ id: doc.id, ...doc.data() });
        });
        
        // Sort: emergency first, then ID
        tokens.sort((a, b) => (b.is_emergency ? 1 : 0) - (a.is_emergency ? 1 : 0));
        
        const nowServing = tokens.filter(t => t.status === 'Serving');
        const upNext = tokens.filter(t => t.status === 'Waiting');

        if (typeof callback === 'function') {
          callback({
            now_serving: nowServing,
            up_next: upNext,
            all_tokens: tokens,
            source: 'firestore_realtime'
          });
        }
      }, (err) => {
        console.warn('Firestore queue listener notice:', err);
      });

      return this.queueUnsubscribe;
    } catch (e) {
      console.warn('Could not attach Firestore queue listener:', e);
      return null;
    }
  }

  /**
   * Uploads file to Firebase Storage with automatic REST fallback
   */
  async uploadFile(file, patientId, folder = 'documents') {
    await this.ensureReady();
    if (this.isReady && this.storage) {
      try {
        const { ref, uploadBytes, getDownloadURL } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-storage.js");
        const filename = `${Date.now()}_${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        const storageRef = ref(this.storage, `patients/${patientId}/${folder}/${filename}`);

        const snapshot = await uploadBytes(storageRef, file);
        const downloadUrl = await getDownloadURL(snapshot.ref);

        return {
          status: 'success',
          storage: 'firebase_client',
          url: downloadUrl,
          filename: filename
        };
      } catch (err) {
        console.warn('Firebase client upload failed, using server fallback:', err);
      }
    }

    // Fallback: Send to Flask server
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);
    formData.append('doc_type', folder === 'xrays' ? 'X-Ray' : 'Consent Form');

    const res = await fetch(`/api/patients/${patientId}/upload`, {
      method: 'POST',
      body: formData
    });
    return await res.json();
  }

  /**
   * Syncs a token document directly into Cloud Firestore
   */
  async syncQueueToken(tokenData) {
    await this.ensureReady();
    if (!this.isReady || !this.db || !tokenData) return false;
    try {
      const { doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      const tokenId = String(tokenData.id || `tok_${Date.now()}`);
      await setDoc(doc(this.db, "queue_tokens", tokenId), {
        id: tokenData.id || tokenId,
        token_number: tokenData.token_number || "Token #001",
        patient_name: tokenData.patient_name || "Walk-in Patient",
        doctor_name: tokenData.doctor_name || "Dr. Sharma",
        chair_name: tokenData.chair_name || "Operatory 1",
        procedure_name: tokenData.procedure_name || "General Consultation",
        status: tokenData.status || "Waiting",
        is_emergency: Boolean(tokenData.is_emergency),
        estimated_wait_min: tokenData.estimated_wait_min || 15,
        updated_at: new Date().toISOString()
      }, { merge: true });
      console.log(`🔥 [Firestore] Token ${tokenData.token_number} synced to Cloud Firestore.`);
      return true;
    } catch (err) {
      console.warn('Firestore token sync error:', err);
      return false;
    }
  }

  /**
   * Syncs patient record into Cloud Firestore
   */
  async syncPatient(patientData) {
    await this.ensureReady();
    if (!this.isReady || !this.db || !patientData) return false;
    try {
      const { doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      const patientDocId = String(patientData.patient_id || patientData.id || `DF-PT-${Date.now()}`);
      await setDoc(doc(this.db, "patients", patientDocId), {
        id: patientData.id,
        patient_id: patientData.patient_id || patientDocId,
        name: patientData.name || "Unknown Patient",
        age: Number(patientData.age || 30),
        gender: patientData.gender || "Male",
        phone: patientData.phone || "",
        email: patientData.email || "",
        blood_group: patientData.blood_group || "B+",
        address: patientData.address || "",
        abdm_health_id: patientData.abdm_health_id || "",
        outstanding_balance: Number(patientData.outstanding_balance || 0),
        total_spent: Number(patientData.total_spent || 0),
        primary_doctor_name: patientData.primary_doctor_name || "Dr. Sharma",
        branch_name: patientData.branch_name || "Downtown Dental",
        critical_alerts: patientData.critical_alerts || [],
        updated_at: new Date().toISOString()
      }, { merge: true });
      console.log(`🔥 [Firestore] Patient ${patientData.name} (${patientDocId}) synced to Cloud Firestore.`);
      return true;
    } catch (err) {
      console.warn('Firestore patient sync error:', err);
      return false;
    }
  }

  /**
   * Firebase Authentication - Register User with Email & Password
   */
  async registerAuthUser(email, password, displayName = '', role = 'patient') {
    await this.ensureReady();
    if (!this.isReady || !this.auth) return null;
    try {
      const { createUserWithEmailAndPassword, updateProfile } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js");
      const userCredential = await createUserWithEmailAndPassword(this.auth, email, password);
      if (displayName) {
        await updateProfile(userCredential.user, { displayName });
      }
      // Store user role doc in Firestore
      const { doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      await setDoc(doc(this.db, "users", userCredential.user.uid), {
        uid: userCredential.user.uid,
        email: email,
        name: displayName || email.split('@')[0],
        role: role,
        created_at: new Date().toISOString(),
        last_sign_in: new Date().toISOString()
      }, { merge: true });

      await this.logAuthEvent({
        email: email,
        name: displayName || email.split('@')[0],
        role: role,
        action: `User registered (${role})`,
        uid: userCredential.user.uid,
        status: "Registered"
      });

      console.log(`🔥 [Firebase Auth] User registered: ${email} (${role})`);
      return userCredential.user;
    } catch (err) {
      if (err.code === 'auth/email-already-in-use') {
        console.log(`ℹ️ [Firebase Auth] User ${email} already exists in Firebase.`);
      } else {
        console.warn('Firebase Auth registration notice:', err);
      }
      return null;
    }
  }

  /**
   * Firebase Authentication - Sign In with Email & Password
   */
  async signInAuthUser(email, password) {
    await this.ensureReady();
    if (!this.isReady) return null;
    try {
      let uid = null;
      if (this.auth) {
        const { signInWithEmailAndPassword } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js");
        const userCredential = await signInWithEmailAndPassword(this.auth, email, password);
        uid = userCredential.user.uid;
        console.log(`🔥 [Firebase Auth] User signed in: ${email}`);
      }

      // Record sign-in event in Firestore 'login_history' collection
      await this.logAuthEvent({
        email: email,
        action: "User signed in successfully",
        uid: uid,
        status: "Success"
      });

      return uid;
    } catch (err) {
      console.warn('Firebase Auth sign-in notice:', err);
      // Still log the sign-in session event
      await this.logAuthEvent({
        email: email,
        action: "User sign-in session recorded",
        status: "Active"
      });
      return null;
    }
  }

  /**
   * Records authentication / sign-in events directly into Firestore 'login_history' collection
   */
  async logAuthEvent(eventData) {
    await this.ensureReady();
    if (!this.isReady || !this.db || !eventData) return false;
    try {
      const { doc, setDoc } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");
      const logId = `sign_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;
      await setDoc(doc(this.db, "login_history", logId), {
        log_id: logId,
        email: eventData.email || "user@dentiflow.com",
        name: eventData.name || eventData.email?.split('@')[0] || "Staff",
        role: eventData.role || "User",
        action: eventData.action || "User signed in successfully",
        module: "Authentication",
        uid: eventData.uid || null,
        timestamp: new Date().toISOString(),
        client_time: new Date().toLocaleString(),
        status: eventData.status || "Success"
      });
      console.log(`🔥 [Firestore] Sign-in event recorded for ${eventData.email} in 'login_history' collection.`);
      return true;
    } catch (err) {
      console.warn('Firestore auth log error:', err);
      return false;
    }
  }
}

// Global instance attached to window
window.DentiFlowFirebase = new DentiFlowFirebaseClient();

// Auto-initialize immediately
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.DentiFlowFirebase.init();
  });
} else {
  window.DentiFlowFirebase.init();
}
