import React, { useState, useEffect } from 'react'
import { Save, AlertCircle, Plus, X, DollarSign, Target, Award, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface ProfileFormProps {
  token: string
  API_BASE: string
}

const standardJobTitles = [
  "Software Engineer",
  "React Developer",
  "FastAPI Developer",
  "Python Developer",
  "DevOps Engineer",
  "Full-Stack Engineer",
  "Machine Learning Engineer",
  "Backend Architect",
  "Frontend Engineer",
  "Data Scientist",
  "Product Manager",
  "Tech Lead",
  "Cloud Solutions Architect",
  "Security Engineer",
  "Site Reliability Engineer"
]

const standardLocations = [
  "Remote",
  "Remote, US",
  "San Francisco, CA",
  "New York, NY",
  "Austin, TX",
  "Seattle, WA",
  "London, UK",
  "Toronto, ON",
  "Berlin, Germany",
  "Paris, France",
  "Singapore",
  "Tokyo, Japan",
  "Boston, MA",
  "Chicago, IL",
  "Denver, CO"
]

export default function ProfileForm({ token, API_BASE }: ProfileFormProps) {
  const [targetTitles, setTargetTitles] = useState<string[]>([])
  const [titleInput, setTitleInput] = useState('')
  const [showTitleDropdown, setShowTitleDropdown] = useState(false)

  const [targetLocations, setTargetLocations] = useState<string[]>([])
  const [locInput, setLocInput] = useState('')
  const [showLocDropdown, setShowLocDropdown] = useState(false)

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

  // Filter lists on-the-fly
  const filteredTitles = standardJobTitles.filter(t => 
    t.toLowerCase().includes(titleInput.toLowerCase()) && 
    !targetTitles.includes(t)
  )

  const filteredLocs = standardLocations.filter(l => 
    l.toLowerCase().includes(locInput.toLowerCase()) && 
    !targetLocations.includes(l)
  )

  return (
    <div className="space-y-10 max-w-[850px] mx-auto">
      {/* Title Header */}
      <div>
        <h1 className="text-3xl font-extrabold font-display tracking-tight text-white mb-2">
          Target <span className="text-accent-primary">Matching Preferences</span>
        </h1>
        <p className="text-slate-400 text-sm font-medium">
          Define semantic weights, titles, locations, and filters. The AI matching engine will rank feeds using these weights.
        </p>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 md:p-10 rounded-2xl border border-slate-800/80 shadow-2xl relative"
      >
        <form onSubmit={handleSave} className="space-y-8">
          
          {/* GRID ROW 1: Titles & Locations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* Target Job Titles Tag Editor with Auto-Suggestion Dropbox */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="h-4 w-4 text-accent-primary" /> Target Job Titles
              </label>
              
              <div className="flex gap-2 relative">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={titleInput}
                    onChange={(e) => {
                      setTitleInput(e.target.value)
                      setShowTitleDropdown(true)
                    }}
                    onFocus={() => setShowTitleDropdown(true)}
                    onBlur={() => setTimeout(() => setShowTitleDropdown(false), 200)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(titleInput, setTitleInput, targetTitles, setTargetTitles))}
                    placeholder="Software Engineer, Tech Lead..."
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                  />
                  {showTitleDropdown && filteredTitles.length > 0 && (
                    <div className="absolute z-50 w-full mt-1.5 bg-slate-900 border border-slate-800 rounded-xl max-h-48 overflow-y-auto shadow-2xl p-1 scrollbar">
                      {filteredTitles.map((title) => (
                        <button
                          key={title}
                          type="button"
                          onClick={() => {
                            if (!targetTitles.includes(title)) {
                              setTargetTitles([...targetTitles, title])
                            }
                            setTitleInput('')
                            setShowTitleDropdown(false)
                          }}
                          className="w-full text-left px-3.5 py-2.5 text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-850 rounded-lg transition-colors duration-200 cursor-pointer"
                        >
                          {title}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => addTag(titleInput, setTitleInput, targetTitles, setTargetTitles)}
                  className="p-2.5 bg-slate-900 border border-slate-855 hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl transition-all self-start h-[42px] cursor-pointer"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 flex-wrap min-h-8">
                {targetTitles.map((t, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center gap-1.5 bg-slate-850/80 border border-slate-800 text-slate-200 px-3 py-1 rounded-full text-xs font-semibold"
                  >
                    <span>{t}</span>
                    <X 
                      className="h-3.5 w-3.5 cursor-pointer text-slate-400 hover:text-danger" 
                      onClick={() => removeTag(t, targetTitles, setTargetTitles)} 
                    />
                  </span>
                ))}
              </div>
            </div>

            {/* Target Locations Tag Editor with Auto-Suggestion Dropbox */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="h-4 w-4 text-accent-primary" /> Target Locations
              </label>
              
              <div className="flex gap-2 relative">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={locInput}
                    onChange={(e) => {
                      setLocInput(e.target.value)
                      setShowLocDropdown(true)
                    }}
                    onFocus={() => setShowLocDropdown(true)}
                    onBlur={() => setTimeout(() => setShowLocDropdown(false), 200)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(locInput, setLocInput, targetLocations, setTargetLocations))}
                    placeholder="Remote, New York, London..."
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                  />
                  {showLocDropdown && filteredLocs.length > 0 && (
                    <div className="absolute z-50 w-full mt-1.5 bg-slate-900 border border-slate-800 rounded-xl max-h-48 overflow-y-auto shadow-2xl p-1 scrollbar">
                      {filteredLocs.map((loc) => (
                        <button
                          key={loc}
                          type="button"
                          onClick={() => {
                            if (!targetLocations.includes(loc)) {
                              setTargetLocations([...targetLocations, loc])
                            }
                            setLocInput('')
                            setShowLocDropdown(false)
                          }}
                          className="w-full text-left px-3.5 py-2.5 text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-850 rounded-lg transition-colors duration-200 cursor-pointer"
                        >
                          {loc}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => addTag(locInput, setLocInput, targetLocations, setTargetLocations)}
                  className="p-2.5 bg-slate-900 border border-slate-855 hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl transition-all self-start h-[42px] cursor-pointer"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 flex-wrap min-h-8">
                {targetLocations.map((l, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center gap-1.5 bg-slate-850/80 border border-slate-800 text-slate-200 px-3 py-1 rounded-full text-xs font-semibold"
                  >
                    <span>{l}</span>
                    <X 
                      className="h-3.5 w-3.5 cursor-pointer text-slate-400 hover:text-danger" 
                      onClick={() => removeTag(l, targetLocations, setTargetLocations)} 
                    />
                  </span>
                ))}
              </div>
            </div>

          </div>

          {/* GRID ROW 2: Salary & Experience */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-slate-800/80 pt-6">
            
            {/* Minimum Desired Salary */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
                Minimum Annual Salary ($)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-slate-500" />
                <input
                  type="number"
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value !== '' ? Number(e.target.value) : '')}
                  placeholder="120000"
                  className="w-full pl-11 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
                  min={0}
                />
              </div>
            </div>

            {/* Experience Level Selector */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="h-4 w-4 text-accent-primary" /> Target Experience Level
              </label>
              <select 
                value={experienceLevel} 
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium cursor-pointer"
              >
                <option value="junior">Junior (Entry-level, Intern)</option>
                <option value="mid">Mid-Level (2-5 years)</option>
                <option value="senior">Senior (5+ years, Architect)</option>
                <option value="lead">Lead (Principal, Staff, Manager)</option>
              </select>
            </div>

          </div>

          {/* GRID ROW 3: Employment Types Checkboxes */}
          <div className="border-t border-slate-800/80 pt-6 space-y-3">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
              Employment Schedule Target
            </label>
            <div className="flex gap-6 flex-wrap">
              {['Full-time', 'Part-time', 'Contract', 'Internship'].map((type) => {
                const checked = jobTypes.includes(type)
                return (
                  <label key={type} className="inline-flex items-center gap-2.5 cursor-pointer text-sm font-semibold text-slate-300 select-none">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleJobType(type)}
                      className="w-4.5 h-4.5 rounded bg-slate-900 border border-slate-800 text-accent-primary focus:ring-accent-primary focus:ring-opacity-20 cursor-pointer"
                    />
                    <span>{type}</span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* GRID ROW 4: Keywords & Exclusions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-slate-800/80 pt-6">
            
            {/* Positive Keywords */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 text-success">
                <CheckCircle2 className="h-4 w-4" /> Score Boost Keywords
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={kwInput}
                  onChange={(e) => setKwInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(kwInput, setKwInput, keywords, setKeywords))}
                  placeholder="Python, React, AWS..."
                  className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-success/60 transition-all text-sm font-medium"
                />
                <button
                  type="button"
                  onClick={() => addTag(kwInput, setKwInput, keywords, setKeywords)}
                  className="p-2.5 bg-slate-900 border border-slate-855 hover:bg-success/15 hover:text-success text-slate-300 rounded-xl transition-all cursor-pointer"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 flex-wrap min-h-8">
                {keywords.map((k, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center gap-1.5 bg-success/5 border border-success/20 text-success px-3 py-1 rounded-full text-xs font-semibold"
                  >
                    <span>{k}</span>
                    <X 
                      className="h-3.5 w-3.5 cursor-pointer text-success/60 hover:text-success" 
                      onClick={() => removeTag(k, keywords, setKeywords)} 
                    />
                  </span>
                ))}
              </div>
            </div>

            {/* Excluded Keywords */}
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 text-danger">
                <ShieldAlert className="h-4 w-4" /> Strict Exclusion Keywords
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={exInput}
                  onChange={(e) => setExInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(exInput, setExInput, excludedKeywords, setExcludedKeywords))}
                  placeholder="PHP, WordPress, Cobalt..."
                  className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-danger/60 transition-all text-sm font-medium"
                />
                <button
                  type="button"
                  onClick={() => addTag(exInput, setExInput, excludedKeywords, setExcludedKeywords)}
                  className="p-2.5 bg-slate-900 border border-slate-855 hover:bg-danger/15 hover:text-danger text-slate-300 rounded-xl transition-all cursor-pointer"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2 flex-wrap min-h-8">
                {excludedKeywords.map((e_kw, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center gap-1.5 bg-danger/5 border border-danger/20 text-danger px-3 py-1 rounded-full text-xs font-semibold"
                  >
                    <span>{e_kw}</span>
                    <X 
                      className="h-3.5 w-3.5 cursor-pointer text-danger/60 hover:text-danger" 
                      onClick={() => removeTag(e_kw, excludedKeywords, setExcludedKeywords)} 
                    />
                  </span>
                ))}
              </div>
            </div>

          </div>

          {/* GRID ROW 5: Resume URL */}
          <div className="border-t border-slate-800/80 pt-6 space-y-3">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-accent-primary" /> Resume / Portfolio URL Link
            </label>
            <input
              type="url"
              value={resumeUrl}
              onChange={(e) => setResumeUrl(e.target.value)}
              placeholder="https://portfolio.me/my-resume.pdf"
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary transition-all text-sm font-medium"
            />
          </div>

          {/* Form Actions Footer Panel */}
          <div className="flex flex-col gap-4 border-t border-slate-800/80 pt-6">
            {msg.text && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`flex items-center gap-3 p-4 rounded-xl text-sm font-semibold border ${
                  msg.type === 'success'
                    ? 'bg-success/5 border-success/20 text-success shadow-glow-success'
                    : 'bg-danger/5 border-danger/20 text-danger shadow-glow-danger'
                }`}
              >
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{msg.text}</span>
              </motion.div>
            )}

            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit" 
              className="px-8 py-3 bg-accent-primary hover:bg-accent-primary/95 hover:shadow-glow-primary text-white font-semibold font-display tracking-wider rounded-xl transition-all duration-300 flex items-center justify-center gap-2 self-end text-xs uppercase disabled:opacity-50 cursor-pointer"
              disabled={saving}
            >
              <Save className="h-4 w-4" />
              <span>{saving ? 'Syncing...' : 'Save Preferences'}</span>
            </motion.button>
          </div>

        </form>
      </motion.div>
    </div>
  )
}
