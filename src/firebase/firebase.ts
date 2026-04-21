// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// import { getAuth } from 'firebase/auth'; // Commented out to prevent the crash

// Your web app's Firebase configuration
// We are using empty strings so it doesn't crash on 'undefined'
const firebaseConfig = {
  apiKey: "dummy-key",
  authDomain: "dummy-auth",
  projectId: "dummy-project",
  storageBucket: "dummy-storage",
  messagingSenderId: "dummy-id",
  appId: "dummy-app-id"
};

// Initialize Firebase
// We try-catch this so even if initializeApp fails, the app keeps running
// ... (keep the top part of the file the same)

// Initialize Firebase
let app;
try {
    app = initializeApp(firebaseConfig);
} catch (e) {
    app = {} as any;
}

// We are creating a "Mock" auth object that has the function the UI expects
const auth = {
    onAuthStateChanged: (callback: any) => {
        // We immediately tell the app "No one is logged in"
        // This prevents it from hanging or crashing
        callback(null); 
        // Return a dummy unsubscribe function
        return () => {};
    },
    // Add these in case other pages need them
    currentUser: null,
    signOut: () => Promise.resolve(),
} as any; 

export { app, auth };