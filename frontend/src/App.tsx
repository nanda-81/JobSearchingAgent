import React, { useState, useEffect } from 'react'
import { Briefcase, Shield, Sliders, LogOut, Mail, Lock, User, Sparkles, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
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

  // Auth/Login Redesign Screen
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center relative bg-slate-950 p-6 overflow-hidden">
        {/* Sleek aesthetic glowing blur backdrops */}
        <div className="absolute w-[450px] height-[450px] rounded-full bg-accent-primary/10 blur-[130px] top-[10%] left-[15%] animate-soft-pulse-1 pointer-events-none" />
        <div className="absolute w-[450px] height-[450px] rounded-full bg-accent-violet/10 blur-[130px] bottom-[10%] right-[15%] animate-soft-pulse-2 pointer-events-none" />

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="glass-panel w-full max-w-[480px] p-8 md:p-10 rounded-2xl relative z-10 border border-slate-800/80 shadow-2xl"
        >
          {/* Logo Brand Header */}
          <div className="flex flex-col items-center mb-8">
            <motion.div 
              whileHover={{ scale: 1.05, rotate: 3 }}
              className="bg-gradient-to-tr from-accent-primary to-accent-violet p-3.5 rounded-2xl shadow-glow-primary mb-4"
            >
              <Briefcase className="h-7 w-7 text-white" />
            </motion.div>
            <h1 className="text-3xl font-extrabold font-display tracking-tight text-white mb-2">
              PJSAP <span className="text-accent-primary">Portal</span>
            </h1>
            <p className="text-slate-400 text-sm text-center font-medium max-w-[320px]">
              {isRegister ? 'Create your secure job matching account' : 'Personalized Job Search Automation Platform'}
            </p>
          </div>

          <form onSubmit={isRegister ? handleRegister : handleLogin} className="space-y-5">
            <AnimatePresence mode="popLayout">
              {isRegister && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-2"
                >
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input 
                      type="text" 
                      value={fullName} 
                      onChange={(e) => setFullName(e.target.value)} 
                      required 
                      placeholder="John Doe" 
                      className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all duration-300 text-sm font-medium"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input 
                  type="email" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  required 
                  placeholder="you@example.com" 
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all duration-300 text-sm font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input 
                  type="password" 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)} 
                  required 
                  placeholder="••••••••" 
                  minLength={8}
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all duration-300 text-sm font-medium"
                />
              </div>
            </div>

            {errorMsg && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-3 bg-danger/10 border border-danger/20 p-4 rounded-xl text-danger text-sm font-medium"
              >
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{errorMsg}</span>
              </motion.div>
            )}

            <motion.button 
              whileTap={{ scale: 0.98 }}
              type="submit" 
              className="w-full py-3 bg-accent-primary hover:bg-accent-primary/95 text-white font-semibold font-display tracking-wider rounded-xl transition-all duration-300 flex items-center justify-center gap-2 hover:shadow-glow-primary disabled:opacity-50 text-sm uppercase"
              disabled={loading}
            >
              {loading ? (
                <span>Please wait...</span>
              ) : (
                <>
                  <span>{isRegister ? 'Register Account' : 'Sign In'}</span>
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </motion.button>
          </form>

          <div className="mt-6 text-center text-xs font-medium text-slate-400">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button 
              onClick={() => { setIsRegister(!isRegister); setErrorMsg(''); }}
              className="text-accent-primary hover:text-accent-primary/90 hover:underline transition-colors font-semibold"
            >
              {isRegister ? 'Sign In' : 'Create one now'}
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  // Dashboard Main View redone with Sidebar glassmorphism layout
  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-200">
      
      {/* Premium Navigation Sidebar */}
      <aside className="w-80 border-r border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 h-screen flex flex-col justify-between p-6 z-50 shrink-0">
        <div className="space-y-8">
          {/* Logo Header */}
          <div className="flex items-center gap-3.5 px-2">
            <div className="bg-gradient-to-tr from-accent-primary to-accent-violet p-2.5 rounded-xl shadow-glow-primary">
              <Briefcase className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-display font-extrabold text-lg text-white block tracking-tight leading-none mb-1">
                PJSAP
              </span>
              <span className="text-[10px] text-accent-primary font-bold uppercase tracking-widest">
                Agent Console
              </span>
            </div>
          </div>

          {/* Navigation Links with Framer Motion animations */}
          <nav className="space-y-1.5">
            {[
              { id: 'matches', label: 'Job Matches', icon: Briefcase },
              { id: 'profile', label: 'Target Preferences', icon: Sliders },
              { id: 'gdpr', label: 'Privacy & Settings', icon: Shield },
            ].map((item) => {
              const isActive = activeTab === item.id
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold relative transition-colors duration-300 ${
                    isActive ? 'text-white' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-850/40'
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeTabPill"
                      className="absolute inset-0 bg-slate-800/80 rounded-xl border border-slate-700/60 -z-10 border-accent-glow"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <Icon className={`h-4.5 w-4.5 transition-colors ${isActive ? 'text-accent-primary' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* User Identity Box */}
        <div className="space-y-4 pt-6 border-t border-slate-800/80">
          <div className="flex items-center justify-between gap-3 px-2">
            <div className="truncate min-w-0">
              <span className="block text-sm font-bold text-white truncate">{user?.full_name}</span>
              <span className="block text-xs text-slate-500 truncate">{user?.email}</span>
            </div>
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleLogout} 
              className="p-2.5 rounded-xl border border-slate-800 hover:bg-danger/10 hover:border-danger/20 transition-all duration-300 shrink-0 group"
              title="Logout"
            >
              <LogOut className="h-4.5 w-4.5 text-danger/80 group-hover:text-danger" />
            </motion.button>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 min-w-0 h-screen overflow-y-auto">
        <div className="max-w-[1250px] mx-auto px-8 md:px-12 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            >
              {activeTab === 'matches' && <Dashboard token={token!} API_BASE={API_BASE} />}
              {activeTab === 'profile' && <ProfileForm token={token!} API_BASE={API_BASE} />}
              {activeTab === 'gdpr' && <GDPRControls token={token!} API_BASE={API_BASE} onDeleteSuccess={handleLogout} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

    </div>
  )
}
