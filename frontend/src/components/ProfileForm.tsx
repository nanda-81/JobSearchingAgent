import React, { useState, useEffect } from 'react'
import { Save, AlertCircle, Plus, X, DollarSign } from 'lucide-react'

interface ProfileFormProps {
  token: string
  API_BASE: string
}

export default function ProfileForm({ token, API_BASE }: ProfileFormProps) {
  const [targetTitles, setTargetTitles] = useState<string[]>([])
  const [titleInput, setTitleInput] = useState('')

  const [targetLocations, setTargetLocations] = useState<string[]>([])
  const [locInput, setLocInput] = useState('')

  const [salaryMin, setSalaryMin] = useState<number | ''>('')
  const [experienceLevel, setExperienceLevel] = useState('mid')

  const [jobTypes, setJobTypes] = useState<string[]>([])

  const [keywords, setKeywords] = useState<string[]>([])
  const [kwInput, setKwInput] = useState('')

  const [excludedKeywords, setExcludedKeywords] = useState<string[]>([])
  const [exInput, setExInput] = useState('')

  const [resumeUrl, setResumeUrl] = useState('')

  const [msg, setMsg] = useState({ text: '', type: '' })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setTargetTitles(data.target_titles || [])
        setTargetLocations(data.target_locations || [])
        setSalaryMin(data.salary_min !== null ? data.salary_min : '')
        setExperienceLevel(data.experience_level || 'mid')
        setJobTypes(data.job_types || [])
        setKeywords(data.keywords || [])
        setExcludedKeywords(data.excluded_keywords || [])
        setResumeUrl(data.resume_url || '')
      }
    } catch {
      setMsg({ text: 'Error fetching targeting settings.', type: 'error' })
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg({ text: '', type: '' })

    try {
      const payload = {
        target_titles: targetTitles,
        target_locations: targetLocations,
        salary_min: salaryMin === '' ? null : Number(salaryMin),
        experience_level: experienceLevel,
        job_types: jobTypes,
        keywords: keywords,
        excluded_keywords: excludedKeywords,
        resume_url: resumeUrl || null
      }

      const res = await fetch(`${API_BASE}/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        setMsg({ text: 'Targeting preferences saved successfully!', type: 'success' })
      } else {
        const err = await res.json()
        setMsg({ text: err.detail || 'Failed to save settings.', type: 'error' })
      }
    } catch {
      setMsg({ text: 'Connection error. Could not reach server.', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  // Tags helper functions
  const addTag = (input: string, setInput: React.Dispatch<React.SetStateAction<string>>, tags: string[], setTags: React.Dispatch<React.SetStateAction<string[]>>) => {
    const cleaned = input.trim()
    if (cleaned && !tags.includes(cleaned)) {
      setTags([...tags, cleaned])
      setInput('')
    }
  }

  const removeTag = (tag: string, tags: string[], setTags: React.Dispatch<React.SetStateAction<string[]>>) => {
    setTags(tags.filter(t => t !== tag))
  }

  const toggleJobType = (type: string) => {
    if (jobTypes.includes(type)) {
      setJobTypes(jobTypes.filter(t => t !== type))
    } else {
      setJobTypes([...jobTypes, type])
    }
  }

  return (
    <div className="glass-card animate-fade-in" style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
        <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)', marginBottom: '8px' }}>Target Preferences</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Define matching criteria. The engine will rank job crawled feeds using these parameters.</p>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

        {/* ROW 1: Titles & Locations */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', flexWrap: 'wrap' }}>
          {/* Target Titles Tag Editor */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Target Job Titles</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(titleInput, setTitleInput, targetTitles, setTargetTitles))}
                placeholder="Software Engineer, Tech Lead..."
              />
              <button
                type="button"
                onClick={() => addTag(titleInput, setTitleInput, targetTitles, setTargetTitles)}
                className="btn btn-secondary"
                style={{ padding: '0 12px' }}
              >
                <Plus size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {targetTitles.map((t, idx) => (
                <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-glass)', padding: '4px 10px', borderRadius: '16px', fontSize: '0.8rem' }}>
                  {t} <X size={12} style={{ cursor: 'pointer', color: 'var(--error)' }} onClick={() => removeTag(t, targetTitles, setTargetTitles)} />
                </span>
              ))}
            </div>
          </div>

          {/* Target Locations Tag Editor */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Target Locations</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input
                type="text"
                value={locInput}
                onChange={(e) => setLocInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(locInput, setLocInput, targetLocations, setTargetLocations))}
                placeholder="Remote, New York, London..."
              />
              <button
                type="button"
                onClick={() => addTag(locInput, setLocInput, targetLocations, setTargetLocations)}
                className="btn btn-secondary"
                style={{ padding: '0 12px' }}
              >
                <Plus size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {targetLocations.map((l, idx) => (
                <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-glass)', padding: '4px 10px', borderRadius: '16px', fontSize: '0.8rem' }}>
                  {l} <X size={12} style={{ cursor: 'pointer', color: 'var(--error)' }} onClick={() => removeTag(l, targetLocations, setTargetLocations)} />
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ROW 2: Salary & Experience */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Minimum Desired Salary ($ / Year)</label>
            <div style={{ position: 'relative' }}>
              <DollarSign size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="number"
                value={salaryMin}
                onChange={(e) => setSalaryMin(e.target.value !== '' ? Number(e.target.value) : '')}
                placeholder="120000"
                style={{ paddingLeft: '32px' }}
                min={0}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Target Experience Level</label>
            <select value={experienceLevel} onChange={(e) => setExperienceLevel(e.target.value)}>
              <option value="junior">Junior (Entry-level, Intern)</option>
              <option value="mid">Mid-Level (2-5 years)</option>
              <option value="senior">Senior (5+ years, Architect)</option>
              <option value="lead">Lead (Principal, Staff, Manager)</option>
            </select>
          </div>
        </div>

        {/* ROW 3: Employment Types */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '12px' }}>Employment Types</label>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            {['Full-time', 'Part-time', 'Contract', 'Internship'].map((type) => {
              const checked = jobTypes.includes(type)
              return (
                <label key={type} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleJobType(type)}
                    style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                  />
                  <span>{type}</span>
                </label>
              )
            })}
          </div>
        </div>

        {/* ROW 4: Keywords & Exclusions */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Positive Keywords */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Positive Keywords (Boost Score)</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input
                type="text"
                value={kwInput}
                onChange={(e) => setKwInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(kwInput, setKwInput, keywords, setKeywords))}
                placeholder="Python, React, AWS..."
              />
              <button
                type="button"
                onClick={() => addTag(kwInput, setKwInput, keywords, setKeywords)}
                className="btn btn-secondary"
                style={{ padding: '0 12px' }}
              >
                <Plus size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {keywords.map((k, idx) => (
                <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '1px solid var(--success)', color: 'var(--success)', padding: '4px 10px', borderRadius: '16px', fontSize: '0.8rem' }}>
                  {k} <X size={12} style={{ cursor: 'pointer' }} onClick={() => removeTag(k, keywords, setKeywords)} />
                </span>
              ))}
            </div>
          </div>

          {/* Excluded Keywords */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Excluded Keywords (Strict Block 0.0 Score)</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input
                type="text"
                value={exInput}
                onChange={(e) => setExInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(exInput, setExInput, excludedKeywords, setExcludedKeywords))}
                placeholder="PHP, WordPress, Cobalt..."
              />
              <button
                type="button"
                onClick={() => addTag(exInput, setExInput, excludedKeywords, setExcludedKeywords)}
                className="btn btn-secondary"
                style={{ padding: '0 12px' }}
              >
                <Plus size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {excludedKeywords.map((e_kw, idx) => (
                <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid var(--error)', color: 'var(--error)', padding: '4px 10px', borderRadius: '16px', fontSize: '0.8rem' }}>
                  {e_kw} <X size={12} style={{ cursor: 'pointer' }} onClick={() => removeTag(e_kw, excludedKeywords, setExcludedKeywords)} />
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Resume URL */}
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>Resume / Portfolio URL</label>
          <input
            type="url"
            value={resumeUrl}
            onChange={(e) => setResumeUrl(e.target.value)}
            placeholder="https://portfolio.me/my-resume.pdf"
          />
        </div>

        {/* Notifications and Submission */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', borderTop: '1px solid var(--border-glass)', paddingTop: '24px' }}>
          {msg.text && (
            <div style={{
              backgroundColor: msg.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${msg.type === 'success' ? 'var(--success)' : 'var(--error)'}`,
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              color: msg.type === 'success' ? 'var(--success)' : 'var(--error)',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertCircle size={16} /> {msg.text}
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-end', padding: '12px 32px' }} disabled={saving}>
            <Save size={16} /> {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>

      </form>
    </div>
  )
}
