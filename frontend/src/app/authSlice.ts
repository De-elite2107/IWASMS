import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { AuthState, User } from '../types'

// Session-only storage — survives normal reload but Ctrl+Shift+R clears it
function loadFromSession(): AuthState {
  try {
    const access = sessionStorage.getItem('iwasms_access')
    const refresh = sessionStorage.getItem('iwasms_refresh')
    const userStr = sessionStorage.getItem('iwasms_user')
    if (access && refresh && userStr) {
      return {
        access,
        refresh,
        user: JSON.parse(userStr),
        isAuthenticated: true,
      }
    }
  } catch {}
  return { user: null, access: null, refresh: null, isAuthenticated: false }
}

const initialState: AuthState = loadFromSession()

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ access: string; refresh: string; user: User }>
    ) => {
      state.access = action.payload.access
      state.refresh = action.payload.refresh
      state.user = action.payload.user
      state.isAuthenticated = true
      sessionStorage.setItem('iwasms_access', action.payload.access)
      sessionStorage.setItem('iwasms_refresh', action.payload.refresh)
      sessionStorage.setItem('iwasms_user', JSON.stringify(action.payload.user))
    },
    updateAccessToken: (state, action: PayloadAction<string>) => {
      state.access = action.payload
      sessionStorage.setItem('iwasms_access', action.payload)
    },
    logout: (state) => {
      state.user = null
      state.access = null
      state.refresh = null
      state.isAuthenticated = false
      sessionStorage.removeItem('iwasms_access')
      sessionStorage.removeItem('iwasms_refresh')
      sessionStorage.removeItem('iwasms_user')
    },
  },
})

export const { setCredentials, updateAccessToken, logout } = authSlice.actions
export default authSlice.reducer
