import React, { useState } from 'react'
import { Key, Shield, Download, Trash2, AlertTriangle, RefreshCw, AlertCircle, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'

interface GDPRControlsProps {
  token: string
  API_BASE: string
  onDeleteSuccess: () => void
}

export default function GDPRControls({ token, API_BASE, onDeleteSuccess }: GDPRControlsProps) {
  // Credentials state
  const [twitterToken, setTwitterToken] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [whatsappPhone, setWhatsappPhone] = useState('')
  const [credsMsg, setCredsMsg] = useState({ text: '', type: '' })
  const [savingCreds, setSavingCreds] = useState(false)

  // Password Visibility toggles
  const [showTwitter, setShowTwitter] = useState(false)
  const [showTelegram, setShowTelegram] = useState(false)
  const [showWhatsapp, setShowWhatsapp] = useState(false)

  // GDPR Actions State
  const [exporting, setExporting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleteChallenge, setDeleteChallenge] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingCreds(true)
    setCredsMsg({ text: '', type: '' })

    try {
      const payload = {
        twitter_token: twitterToken || null,
        telegram_chat_id: telegramChatId || null,
        whatsapp_phone: whatsappPhone || null
      }

      const res = await fetch(`${API_BASE}/social/credentials`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        setCredsMsg({ text: 'Credentials securely encrypted and updated successfully.', type: 'success' })
        setTwitterToken('')
        setTelegramChatId('')
        setWhatsappPhone('')
      } else {
        const err = await res.json()
        setCredsMsg({ text: err.detail || 'Failed to update credentials.', type: 'error' })
      }
    } catch {
      setCredsMsg({ text: 'Connection failed.', type: 'error' })
    } finally {
      setSavingCreds(false)
    }
  }

  const handleGDPRDataExport = async () => {
    setExporting(true)
    try {
      const res = await fetch(`${API_BASE}/gdpr/export`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()

        const jsonStr = JSON.stringify(data, null, 2)
        const blob = new Blob([jsonStr], { type: 'application/json' })
        const downloadUrl = URL.createObjectURL(blob)

        const anchor = document.createElement('a')
        anchor.href = downloadUrl
        anchor.download = 'pjsap_subject_access_data.json'
        document.body.appendChild(anchor)
        anchor.click()
        anchor.remove()

        URL.revokeObjectURL(downloadUrl)
      } else {
        alert('Data export failed. Session expired?')
      }
    } catch {
      alert('Failed to connect to export gateway.')
    } finally {
      setExporting(false)
    }
  }

  const handleGDPRForgottenDelete = async (e: React.FormEvent) => {
    e.preventDefault()
    if (deleteChallenge !== 'DELETE') {
      setDeleteError("Verification challenge mismatch. Please type exactly 'DELETE'.")
      return
    }

    setDeleting(true)
    setDeleteError('')
    try {
      const res = await fetch(`${API_BASE}/gdpr/delete`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        alert('All personal profiles and credentials deleted permanently.')
        onDeleteSuccess()
      } else {
        const err = await res.json()
        setDeleteError(err.detail || 'Failed to scrub profile.')
      }
    } catch {
      setDeleteError('Connection error.')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-10 max-w-[850px] mx-auto">
      
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold font-display tracking-tight text-white mb-2">
          Privacy & <span className="text-accent-primary">Secure Settings</span>
        </h1>
        <p className="text-slate-400 text-sm font-medium">
          Manage at-rest encryption nodes, GDPR access portability, and permanent profile scrub zones.
        </p>
      </div>

      <div className="space-y-8">
        
        {/* SECTION 1: Credentials Encryption */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 md:p-10 rounded-2xl border border-slate-800/80 shadow-2xl relative"
        >
          <div className="border-b border-slate-800/80 pb-5 mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2 leading-none">
              <Key className="h-5 w-5 text-accent-primary" /> Secure API Credentials
            </h2>
            <p className="text-slate-400 text-xs font-semibold">
              Tokens and keys are salted and encrypted symmetrically using **AES-256-GCM** at rest before syncing to channels.
            </p>
          </div>

          <form onSubmit={handleSaveCredentials} className="space-y-6">
            
            {/* Input 1: Twitter */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                Twitter OAuth2 Token
              </label>
              <div className="relative">
                <input
                  type={showTwitter ? 'text' : 'password'}
                  value={twitterToken}
                  onChange={(e) => setTwitterToken(e.target.value)}
                  placeholder="••••••••••••••••••••"
                  className="w-full pl-4 pr-12 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowTwitter(!showTwitter)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showTwitter ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Input 2: Telegram */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                Telegram Chat ID
              </label>
              <div className="relative">
                <input
                  type={showTelegram ? 'text' : 'password'}
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                  placeholder="e.g. 54321098"
                  className="w-full pl-4 pr-12 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowTelegram(!showTelegram)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showTelegram ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Input 3: WhatsApp */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                WhatsApp Phone Number
              </label>
              <div className="relative">
                <input
                  type={showWhatsapp ? 'text' : 'password'}
                  value={whatsappPhone}
                  onChange={(e) => setWhatsappPhone(e.target.value)}
                  placeholder="e.g. +15551234567"
                  className="w-full pl-4 pr-12 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowWhatsapp(!showWhatsapp)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showWhatsapp ? <EyeOff className="h-4.5 w-4.5" /> : <Eye className="h-4.5 w-4.5" />}
                </button>
              </div>
            </div>

            {/* Status alerts */}
            {credsMsg.text && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`flex items-center gap-3 p-4 rounded-xl text-sm font-semibold border ${
                  credsMsg.type === 'success'
                    ? 'bg-success/5 border-success/20 text-success shadow-glow-success'
                    : 'bg-danger/5 border-danger/20 text-danger shadow-glow-danger'
                }`}
              >
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{credsMsg.text}</span>
              </motion.div>
            )}

            {/* Form button */}
            <div className="flex justify-end pt-2">
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit" 
                className="px-6 py-2.5 bg-accent-primary hover:bg-accent-primary/95 text-white font-semibold font-display tracking-wider rounded-xl hover:shadow-glow-primary transition-all text-xs uppercase disabled:opacity-50"
                disabled={savingCreds}
              >
                {savingCreds ? 'Encrypting...' : 'Update & Encrypt Credentials'}
              </motion.button>
            </div>
          </form>
        </motion.div>

        {/* SECTION 2: GDPR Subject Access SAR */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 md:p-10 rounded-2xl border border-slate-800/80 shadow-2xl relative"
        >
          <div className="border-b border-slate-800/80 pb-5 mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-2 leading-none">
              <Shield className="h-5 w-5 text-accent-violet" /> Subject Access Portability (SAR)
            </h2>
            <p className="text-slate-400 text-xs font-semibold">
              Exercise your data rights under GDPR Article 20. Instantly pack all vectors, target criteria, credentials, and match metrics into a downloadable JSON file.
            </p>
          </div>

          <div className="flex justify-between items-center flex-wrap gap-4 pt-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 bg-slate-900 border border-slate-850 px-3 py-1.5 rounded-lg">
              <ShieldCheck className="h-4 w-4 text-accent-violet" /> Compliance Standard: GDPR (Regulation (EU) 2016/679)
            </span>
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleGDPRDataExport} 
              className="px-5 py-2.5 bg-slate-900 border border-slate-850 hover:bg-slate-800 hover:text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center gap-2"
              disabled={exporting}
            >
              {exporting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Packing Data...</span>
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  <span>Download Access Package</span>
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* SECTION 3: GDPR Right to Forgotten Purge (Danger Zone) */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 md:p-10 rounded-2xl border border-danger/35 shadow-2xl relative bg-danger/[0.01]"
        >
          <div className="border-b border-slate-800/80 pb-5 mb-6">
            <h2 className="text-lg font-bold text-danger flex items-center gap-2 mb-2 leading-none">
              <Trash2 className="h-5 w-5" /> Cascading Scrub Zone (Right to be Forgotten)
            </h2>
            <p className="text-slate-400 text-xs font-semibold">
              Wipe all settings, credentials, resumes, matching vectors, and login records cascadingly. This action scrubbed instantly is irreversible.
            </p>
          </div>

          {!confirmDelete ? (
            <motion.button 
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => setConfirmDelete(true)} 
              className="px-6 py-2.5 bg-danger hover:bg-danger/95 hover:shadow-glow-danger text-white text-xs font-bold uppercase tracking-wider rounded-xl transition-all"
            >
              Scrub My Account & Scrub Records
            </motion.button>
          ) : (
            <form onSubmit={handleGDPRForgottenDelete} className="space-y-6">
              <div className="flex gap-4 p-5 bg-danger/5 border border-danger/25 rounded-2xl">
                <AlertTriangle className="h-8 w-8 text-danger shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <strong className="block text-sm font-bold text-danger">Cascading Database Scrub Confirmation</strong>
                  <p className="text-xs font-medium text-slate-400 leading-relaxed">
                    This triggers cascading purges across PostgreSQL nodes, scraping targeting matrices, profile parameters, resumes, and credentials. Internal audit hashes will be anonymized.
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-300">
                  Please type exactly <strong className="text-white">DELETE</strong> to authorize scrub cascade:
                </label>
                <input
                  type="text"
                  value={deleteChallenge}
                  onChange={(e) => setDeleteChallenge(e.target.value)}
                  required
                  placeholder="DELETE"
                  className="w-full max-w-[280px] px-4 py-2.5 bg-slate-900 border border-danger/35 focus:border-danger rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-danger/20 transition-all text-sm font-medium"
                />
              </div>

              {deleteError && (
                <div className="text-danger text-xs font-semibold flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  <span>{deleteError}</span>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <motion.button 
                  whileTap={{ scale: 0.98 }}
                  type="submit" 
                  className="px-5 py-2.5 bg-danger hover:bg-danger/95 text-white text-xs font-bold uppercase tracking-wider rounded-xl transition-all"
                  disabled={deleting}
                >
                  {deleting ? 'Scrubbing...' : 'Scrub Cascadingly'}
                </motion.button>
                <motion.button 
                  whileTap={{ scale: 0.98 }}
                  type="button" 
                  onClick={() => { setConfirmDelete(false); setDeleteChallenge(''); setDeleteError(''); }}
                  className="px-5 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-bold uppercase tracking-wider rounded-xl transition-all"
                >
                  Cancel
                </motion.button>
              </div>
            </form>
          )}
        </motion.div>

      </div>

    </div>
  )
}
