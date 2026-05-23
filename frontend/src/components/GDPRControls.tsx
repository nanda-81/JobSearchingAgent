import React, { useState } from 'react'
import { Key, Shield, Download, Trash2, AlertTriangle, Check, RefreshCw } from 'lucide-react'

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
        // Clear forms for safety
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
        
        # Build dynamic browser download
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '40px', maxWidth: '800px', margin: '0 auto' }}>
      
      {/* SECTION 1: Credentials Encryption */}
      <div className="glass-card animate-fade-in" style={{ padding: '40px' }}>
        <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Key size={22} color="var(--primary)" /> Secure API Credentials
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Add credentials for automated channel alerts. Tokens are encrypted using symmetric AES-256 at-rest.
          </p>
        </div>

        <form onSubmit={handleSaveCredentials} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Twitter OAuth2 Token</label>
            <input 
              type="password" 
              value={twitterToken} 
              onChange={(e) => setTwitterToken(e.target.value)} 
              placeholder="••••••••••••••••••••" 
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Telegram Chat ID</label>
            <input 
              type="password" 
              value={telegramChatId} 
              onChange={(e) => setTelegramChatId(e.target.value)} 
              placeholder="e.g. 54321098" 
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>WhatsApp Phone Number</label>
            <input 
              type="password" 
              value={whatsappPhone} 
              onChange={(e) => setWhatsappPhone(e.target.value)} 
              placeholder="e.g. +15551234567" 
            />
          </div>

          {credsMsg.text && (
            <div style={{ 
              backgroundColor: credsMsg.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
              border: `1px solid ${credsMsg.type === 'success' ? 'var(--success)' : 'var(--error)'}`, 
              padding: '12px', 
              borderRadius: 'var(--radius-sm)', 
              color: credsMsg.type === 'success' ? 'var(--success)' : 'var(--error)', 
              fontSize: '0.85rem' 
            }}>
              {credsMsg.text}
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-end' }} disabled={savingCreds}>
            {savingCreds ? 'Encrypting...' : 'Update & Encrypt Credentials'}
          </button>
        </form>
      </div>

      {/* SECTION 2: GDPR Subject Access SAR */}
      <div className="glass-card animate-fade-in" style={{ padding: '40px' }}>
        <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Shield size={22} color="var(--accent)" /> GDPR Subject Access & Portability
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Request data records. Download all targeting criteria, logs, matching statistics, and user account records in standard JSON.
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Compliance Standard: GDPR (Regulation (EU) 2016/679) Article 20.
          </div>
          <button onClick={handleGDPRDataExport} className="btn btn-secondary" disabled={exporting}>
            {exporting ? (
              <><RefreshCw size={16} className="animate-spin" /> Exporting File...</>
            ) : (
              <><Download size={16} /> Download Personal JSON Package</>
            )}
          </button>
        </div>
      </div>

      {/* SECTION 3: GDPR Right to Forgotten Purge */}
      <div className="glass-card animate-fade-in" style={{ padding: '40px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
        <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Trash2 size={22} color="var(--error)" /> Danger Zone: Permanent Account Deletion
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Exercise Right to be Forgotten. Wipe all personal data, credentials, resumes, and matches cascadingly. This action is irreversible.
          </p>
        </div>

        {!confirmDelete ? (
          <button onClick={() => setConfirmDelete(true)} className="btn btn-danger">
            <Trash2 size={16} /> Delete Account & Scrub All Records
          </button>
        ) : (
          <form onSubmit={handleGDPRForgottenDelete} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', gap: '12px', padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.05)', border: '1px dashed var(--error)', borderRadius: 'var(--radius-sm)' }}>
              <AlertTriangle size={32} color="var(--error)" style={{ flexShrink: 0 }} />
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem', color: 'var(--error)', marginBottom: '4px' }}>Confirm Permanent Purge</strong>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  This cascades into PostgreSQL, scrubbing user settings, social credentials, matching logs, and resumes forever. Audit logs are anonymized.
                </span>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Please type exactly <strong style={{ color: 'var(--text-primary)' }}>DELETE</strong> to confirm:
              </label>
              <input 
                type="text" 
                value={deleteChallenge} 
                onChange={(e) => setDeleteChallenge(e.target.value)} 
                required 
                placeholder="DELETE" 
                style={{ borderColor: 'var(--error)', maxWidth: '300px' }}
              />
            </div>

            {deleteError && (
              <div style={{ color: 'var(--error)', fontSize: '0.85rem' }}>{deleteError}</div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button type="submit" className="btn btn-danger" disabled={deleting}>
                {deleting ? 'Scrubbing...' : 'Confirm Permanent Deletion'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => { setConfirmDelete(false); setDeleteChallenge(''); setDeleteError(''); }}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

    </div>
  )
}
