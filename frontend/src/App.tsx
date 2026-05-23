import React, { useState, useEffect } from 'react'
import { Briefcase, Settings, Shield, User, LogOut, Key } from 'lucide-react'
import Dashboard from './components/Dashboard'
import ProfileForm from './components/ProfileForm'
import GDPRControls from './components/GDPRControls'

interface UserSession {
  email: string
  full_name: string
}

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('pjsap_token'))
  const [user, setUser] = useState<UserSession | null>(null)
  const [activeTab, setActiveTab] = useState<'matches' | 'profile' | 'gdpr'>('matches')
  
  // Auth Form State
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  // API base path
  const API_BASE = 'http://localhost:8000/api/v1'

  useEffect(() => {
    if (token) {
      fetchUserProfile()
    } else {
      setUser(null)
    }
  }, [token])

  const fetchUserProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setUser({ email: data.email, full_name: data.full_name })
      } else {
        // Token expired or invalid
        handleLogout()
      }
    } catch {
      handleLogout()
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setLoading(true)
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        localStorage.setItem('pjsap_token', data.access_token)
        setToken(data.access_token)
      } else {
        const err = await res.json()
        setErrorMsg(err.detail || 'Authentication failed. Please verify credentials.')
      }
    } catch {
      setErrorMsg('Cannot connect to backend server. Is it running?')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      })

      if (res.ok) {
        // Auto-login after registration
        setIsRegister(false)
        await handleLogin(e)
      } else {
        const err = await res.json()
        setErrorMsg(err.detail || 'Registration failed. Check password length (min 8 chars).')
      }
    } catch {
      setErrorMsg('Cannot connect to backend server.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('pjsap_token')
    setToken(null)
    setUser(null)
    setActiveTab('matches')
    setErrorMsg('')
  }

  if (!token) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', padding: '16px' }}>
        {/* Glowing blur background effects */}
        <div className="brand-gradient" style={{ position: 'absolute', width: '300px', height: '300px', borderRadius: '50%', filter: 'blur(100px)', opacity: '0.15', top: '15%', left: '20%' }} />
        <div style={{ position: 'absolute', width: '300px', height: '300px', borderRadius: '50%', filter: 'blur(100px)', opacity: '0.15', bottom: '15%', right: '20%', backgroundColor: 'var(--accent)' }} />

        <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '440px', padding: '40px', position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '32px' }}>
            <div className="brand-gradient" style={{ width: '56px', height: '56px', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-glow)', marginBottom: '16px' }}>
              <Briefcase size={28} color="white" />
            </div>
            <h1 className="text-gradient" style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>PJSAP Portal</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px', textAlign: 'center' }}>
              {isRegister ? 'Create your secure job matching account' : 'Personalized Job Search Automation Platform'}
            </p>
          </div>

          <form onSubmit={isRegister ? handleRegister : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {isRegister && (
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Full Name</label>
                <input 
                  type="text" 
                  value={fullName} 
                  onChange={(e) => setFullName(e.target.value)} 
                  required 
                  placeholder="John Doe" 
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Email Address</label>
              <input 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
                placeholder="you@example.com" 
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Password</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                placeholder="••••••••" 
                minLength={8}
              />
            </div>

            {errorMsg && (
              <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', padding: '12px', borderRadius: 'var(--radius-sm)', color: 'var(--error)', fontSize: '0.85rem' }}>
                {errorMsg}
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '14px' }} disabled={loading}>
              {loading ? 'Please wait...' : (isRegister ? 'Register Account' : 'Sign In')}
            </button>
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>
              {isRegister ? 'Already have an account?' : "Don't have an account?"}
            </span>{' '}
            <button 
              onClick={() => { setIsRegister(!isRegister); setErrorMsg(''); }}
              style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontWeight: 500 }}
            >
              {isRegister ? 'Sign In' : 'Create one now'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Sleek Header Bar */}
      <header className="glass-card" style={{ borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderTop: 'none', position: 'sticky', top: 0, zIndex: 100, backdropFilter: 'blur(20px)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          
          {/* Brand Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="brand-gradient" style={{ width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 10px var(--primary-glow)' }}>
              <Briefcase size={20} color="white" />
            </div>
            <div>
              <span className="text-gradient" style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.25rem', display: 'block', lineHeight: 1 }}>PJSAP</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Agent Console</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={() => setActiveTab('matches')} 
              className={`btn ${activeTab === 'matches' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <Briefcase size={16} /> Job Matches
            </button>

            <button 
              onClick={() => setActiveTab('profile')} 
              className={`btn ${activeTab === 'profile' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <User size={16} /> Target Preferences
            </button>

            <button 
              onClick={() => setActiveTab('gdpr')} 
              className={`btn ${activeTab === 'gdpr' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <Shield size={16} /> Privacy & Settings
            </button>
          </nav>

          {/* Logged in Identity info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ textAlign: 'right', display: 'none', sm: 'block' }}>
              <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500 }}>{user?.full_name}</span>
              <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.email}</span>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '10px', borderRadius: '50%' }} title="Logout">
              <LogOut size={16} color="var(--error)" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Body container */}
      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '40px 24px' }}>
        {activeTab === 'matches' && <Dashboard token={token} API_BASE={API_BASE} />}
        {activeTab === 'profile' && <ProfileForm token={token} API_BASE={API_BASE} />}
        {activeTab === 'gdpr' && <GDPRControls token={token} API_BASE={API_BASE} onDeleteSuccess={handleLogout} />}
      </main>
    </div>
  )
}
