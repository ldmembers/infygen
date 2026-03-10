// hooks/useAuth.ts
// Firebase auth state — exposes user, loading, login, logout.

import { useState, useEffect } from 'react'
import { type User, onAuthStateChanged, signInWithEmailAndPassword } from 'firebase/auth'
import { auth, googleProvider, signInWithPopup, signOut } from '@/config/firebase'
import { normaliseError } from '@/utils/errorHandler'

interface AuthState {
  user:         User | null
  loading:      boolean
  error:        string | null
}

interface AuthActions {
  loginWithGoogle:   () => Promise<void>
  loginWithEmail:    (email: string, password: string) => Promise<void>
  logout:            () => Promise<void>
  clearError:        () => void
}

export function useAuth(): AuthState & AuthActions {
  const [user,    setUser]    = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  async function loginWithGoogle() {
    setError(null)
    try {
      await signInWithPopup(auth, googleProvider)
    } catch (e) {
      setError(normaliseError(e))
    }
  }

  async function loginWithEmail(email: string, password: string) {
    setError(null)
    try {
      await signInWithEmailAndPassword(auth, email, password)
    } catch (e) {
      setError(normaliseError(e))
    }
  }

  async function logout() {
    await signOut(auth)
  }

  return { user, loading, error, loginWithGoogle, loginWithEmail, logout, clearError: () => setError(null) }
}
