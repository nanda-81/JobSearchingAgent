import { useState } from 'react'
import { ExternalLink, Bookmark, Check, Trash2, Calendar, MapPin, Building, ChevronDown, ChevronUp, Sparkles, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export interface Job {
  id: string
  title: string
  company: string
  location: string
  is_remote: boolean
  description: string
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  url: string
  posted_at: string
}

export interface Match {
  job: Job
  match_score: number
  matching_details: {
    title_match?: number
    location_match?: number
    salary_match?: number
    experience_match?: number
    semantic_match?: number
    matched_keywords?: string[]
    reasons?: string[]
    blocked?: boolean
    reason?: string
  }
  status: string
}

interface JobListProps {
  matches: Match[]
  onStatusUpdate: (jobId: string, newStatus: string) => void
  token: string
  API_BASE: string
}

export default function JobList({ matches, onStatusUpdate, token, API_BASE }: JobListProps) {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null)
  const [csvLoadingId, setCsvLoadingId] = useState<string | null>(null)

  const handleAddToCSV = async (jobId: string) => {
    setCsvLoadingId(jobId)
    try {
      const res = await fetch(`${API_BASE}/matches/${jobId}/export-to-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (res.ok) {
        const data = await res.json()
        alert(`📂 ${data.message}\nSaved at: ${data.file_path}`)
      } else {
        const err = await res.json()
        alert(`⚠️ Failed: ${err.detail || 'Could not write to local CSV'}`)
      }
    } catch {
      alert("⚠️ Error connecting to server spreadsheet endpoint.")
    } finally {
      setCsvLoadingId(null)
    }
  }

  const getScoreTheme = (score: number) => {
    const percent = score * 100
    if (percent >= 80) return {
      color: '#10b981', // Emerald
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.25)',
      glow: '0 0 15px rgba(16, 185, 129, 0.15)'
    }
    if (percent >= 50) return {
      color: '#f59e0b', // Amber
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.25)',
      glow: '0 0 15px rgba(245, 158, 11, 0.12)'
    }
    return {
      color: '#0ea5e9', // Steel-blue
      bg: 'rgba(14, 165, 233, 0.1)',
      border: 'rgba(14, 165, 233, 0.25)',
      glow: '0 0 15px rgba(14, 165, 233, 0.15)'
    }
  }

  const formatRelativeDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diffTime = Math.abs(now.getTime() - date.getTime())
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays <= 1) return 'Today'
      if (diffDays === 2) return 'Yesterday'
      return `${diffDays} days ago`
    } catch {
      return 'Recent'
    }
  }

  if (matches.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-20 bg-slate-900/40 border border-slate-800/80 rounded-2xl"
      >
        <AlertCircle className="h-10 w-10 text-slate-500 mx-auto mb-4" />
        <h3 className="text-base font-bold text-white mb-1">No matches found yet</h3>
        <p className="text-slate-400 text-xs font-medium max-w-[340px] mx-auto">
          Verify target preferences are configured or dispatch the crawler pipelines manually using the buttons above.
        </p>
      </motion.div>
    )
  }

  const listContainerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 25 } }
  }

  return (
    <motion.div 
      variants={listContainerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {matches.map((match) => {
        const job = match.job
        const percent = Math.round(match.match_score * 100)
        const isExpanded = expandedMatchId === job.id
        const scoreTheme = getScoreTheme(match.match_score)

        return (
          <motion.div 
            key={job.id}
            variants={itemVariants}
            whileHover={{ scale: 1.01, translateY: -2 }}
            transition={{ duration: 0.2 }}
            className="glass-panel p-6 rounded-2xl relative overflow-hidden transition-all duration-300 hover:border-slate-700/80 hover:shadow-glow-primary border-l-4"
            style={{ borderLeftColor: scoreTheme.color }}
          >
            {/* Header section: Titles & badges */}
            <div className="flex justify-between items-start flex-wrap gap-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white mb-2 leading-snug tracking-tight">
                  {job.title}
                </h3>
                
                <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-semibold text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Building className="h-4 w-4 text-slate-500" /> {job.company}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <MapPin className="h-4 w-4 text-slate-500" /> {job.location}
                    {job.is_remote && (
                      <span className="ml-2 px-2 py-0.5 bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-[9px] font-bold uppercase rounded-md tracking-wider">
                        Remote
                      </span>
                    )}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4 text-slate-500" /> {formatRelativeDate(job.posted_at)}
                  </span>
                </div>
              </div>

              {/* Match Relevancy Badge with gradient glow */}
              <div 
                className="px-4 py-1.5 text-xs font-extrabold rounded-full flex items-center gap-1.5 tracking-wider border text-white"
                style={{ 
                  backgroundColor: scoreTheme.bg,
                  borderColor: scoreTheme.border,
                  boxShadow: scoreTheme.glow,
                  color: scoreTheme.color
                }}
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{percent}% Match</span>
              </div>
            </div>

            {/* Description Preview (Clean) */}
            <p className="text-slate-400 text-sm font-medium leading-relaxed mb-4 line-clamp-2">
              {job.description ? job.description.replace(/<[^>]*>/g, '') : 'No description provided.'}
            </p>

            {/* Salary block if exists */}
            {(job.salary_min || job.salary_max) && (
              <div className="mb-4 inline-flex items-center px-3 py-1 bg-success/5 border border-success/15 rounded-lg text-xs font-bold text-success">
                Estimated Salary: {job.salary_currency || 'USD'} {job.salary_min ? job.salary_min.toLocaleString() : 'N/A'} - {job.salary_max ? job.salary_max.toLocaleString() : 'N/A'}
              </div>
            )}

            {/* Expander Drawer trigger */}
            <div className="border-t border-slate-800/80 pt-4 mt-2">
              <button 
                onClick={() => setExpandedMatchId(isExpanded ? null : job.id)}
                className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-accent-primary hover:text-accent-primary/95 hover:underline transition-colors"
              >
                {isExpanded ? (
                  <>
                    <span>Hide Matching Analytics</span>
                    <ChevronUp className="h-3.5 w-3.5" />
                  </>
                ) : (
                  <>
                    <span>Inspect Target Requirements</span>
                    <ChevronDown className="h-3.5 w-3.5" />
                  </>
                )}
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                    className="overflow-hidden mt-4 space-y-6"
                  >
                    {/* High-Fidelity Job description block */}
                    <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-5 max-h-[350px] overflow-y-auto">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-1.5">
                        📋 Position Description & Profile
                      </h4>
                      <div 
                        className="job-html-description text-slate-300 text-sm font-medium leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: job.description }}
                      />
                    </div>

                    {/* Matching Engine Details */}
                    <div className="bg-accent-indigoGlow border border-accent-primary/20 rounded-xl p-5">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-accent-primary mb-3 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5" /> Vector Engine Match Reasoning
                      </h4>
                      
                      <ul className="space-y-2 text-slate-300 text-xs font-medium">
                        {match.matching_details.reasons?.map((reason, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-success font-extrabold shrink-0">✓</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>

                      {match.matching_details.matched_keywords && match.matching_details.matched_keywords.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-800/60">
                          <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                            Matched Tokens:
                          </span>
                          <div className="flex gap-2 flex-wrap">
                            {match.matching_details.matched_keywords.map((kw, i) => (
                              <span 
                                key={i} 
                                className="bg-accent-primary/10 border border-accent-primary/20 text-accent-primary px-2.5 py-1 rounded-md text-[10px] font-bold"
                              >
                                {kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Action buttons drawer */}
            <div className="flex justify-between items-center flex-wrap gap-4 border-t border-slate-800/80 pt-4 mt-4">
              
              {/* Left actions block */}
              <div className="flex gap-2.5 flex-wrap items-center">
                {match.status !== 'saved' && match.status !== 'applied' && (
                  <motion.button 
                    whileTap={{ scale: 0.96 }}
                    onClick={() => onStatusUpdate(job.id, 'saved')}
                    className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center gap-2"
                  >
                    <Bookmark className="h-4 w-4 text-slate-400" />
                    <span>Save Job</span>
                  </motion.button>
                )}
                {match.status === 'saved' && (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-success bg-success/5 border border-success/15 px-3 py-2 rounded-xl">
                    <Check className="h-4 w-4" />
                    <span>Saved to Feed</span>
                  </span>
                )}
                <motion.button 
                  whileTap={{ scale: 0.96 }}
                  onClick={() => onStatusUpdate(job.id, 'dismissed')}
                  className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:text-danger rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4 text-slate-500" />
                  <span>Dismiss</span>
                </motion.button>

                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={() => handleAddToCSV(job.id)}
                  disabled={csvLoadingId === job.id}
                  className="px-4 py-2 bg-slate-900 border border-accent-primary/20 hover:border-accent-primary/40 text-accent-primary hover:bg-accent-primary/5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>{csvLoadingId === job.id ? "Syncing..." : "Add to CSV Tracker"}</span>
                </motion.button>
              </div>

              {/* Apply now link */}
              <motion.a 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                href={job.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-5 py-2.5 bg-accent-primary text-white shadow-glow-primary hover:bg-accent-primary/95 text-xs font-bold uppercase tracking-wider rounded-xl transition-all duration-300 flex items-center gap-2"
              >
                <span>Apply Now</span>
                <ExternalLink className="h-4 w-4" />
              </motion.a>
            </div>

          </motion.div>
        )
      })}
    </motion.div>
  )
}
