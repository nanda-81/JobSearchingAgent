import React, { useState } from 'react'
import { ExternalLink, Bookmark, Check, Trash2, Calendar, MapPin, Building, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'

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
}

export default function JobList({ matches, onStatusUpdate }: JobListProps) {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null)

  const getScoreColor = (score: number) => {
    const percent = score * 100
    if (percent >= 80) return 'var(--success)'
    if (percent >= 50) return 'var(--warning)'
    return 'var(--accent)'
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
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
        <p style={{ fontSize: '1.1rem', marginBottom: '8px' }}>No matches found yet.</p>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Try running a manual job search above or update your target matching preferences.</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {matches.map((match) => {
        const job = match.job
        const percent = Math.round(match.match_score * 100)
        const isExpanded = expandedMatchId === job.id
        const scoreColor = getScoreColor(match.match_score)

        return (
          <div 
            key={job.id} 
            className="glass-card animate-fade-in" 
            style={{ 
              padding: '24px', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '16px',
              borderLeft: `4px solid ${scoreColor}`
            }}
          >
            {/* Upper row: Title, company, score */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', marginBottom: '8px' }}>{job.title}</h3>
                
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <Building size={14} /> {job.company}
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <MapPin size={14} /> {job.location}
                    {job.is_remote && (
                      <span className="brand-gradient" style={{ padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', color: 'white', fontWeight: 600, marginLeft: '6px' }}>
                        Remote
                      </span>
                    )}
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <Calendar size={14} /> {formatRelativeDate(job.posted_at)}
                  </span>
                </div>
              </div>

              {/* Match Relevancy Badge */}
              <div 
                style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '6px', 
                  backgroundColor: 'rgba(15, 23, 42, 0.4)', 
                  border: `1px solid ${scoreColor}`, 
                  padding: '6px 14px', 
                  borderRadius: '20px',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  color: scoreColor,
                  boxShadow: `0 0 10px ${scoreColor}20`
                }}
              >
                <Sparkles size={14} />
                <span>{percent}% Match</span>
              </div>
            </div>

            {/* Description Preview */}
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', WebkitLineClamp: 2, display: '-webkit-box', WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {job.description}
            </p>

            {/* Salary block if exists */}
            {(job.salary_min || job.salary_max) && (
              <div style={{ fontSize: '0.85rem', color: 'var(--success)', fontWeight: 500 }}>
                Estimated Salary: {job.salary_currency || 'USD'} {job.salary_min ? job.salary_min.toLocaleString() : 'N/A'} - {job.salary_max ? job.salary_max.toLocaleString() : 'N/A'}
              </div>
            )}

            {/* Matching Engine details toggler */}
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px' }}>
              <button 
                onClick={() => setExpandedMatchId(isExpanded ? null : job.id)}
                style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 500 }}
              >
                {isExpanded ? (
                  <>Hide Matching Score Explanation <ChevronUp size={14} /></>
                ) : (
                  <>Show Matching Score Explanation <ChevronDown size={14} /></>
                )}
              </button>

              {isExpanded && (
                <div style={{ marginTop: '16px', padding: '16px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Match Analytics Breakdown
                  </h4>
                  
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {match.matching_details.reasons?.map((reason, idx) => (
                      <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                        <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>

                  {match.matching_details.matched_keywords && match.matching_details.matched_keywords.length > 0 && (
                    <div style={{ marginTop: '14px' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Matched Keywords:</span>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {match.matching_details.matched_keywords.map((kw, i) => (
                          <span key={i} style={{ backgroundColor: 'rgba(6, 182, 212, 0.1)', border: '1px solid var(--accent)', color: 'var(--accent)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem' }}>
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action buttons footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderTop: '1px solid var(--border-glass)', paddingTop: '16px', marginTop: '4px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                {match.status !== 'saved' && match.status !== 'applied' && (
                  <button 
                    onClick={() => onStatusUpdate(job.id, 'saved')}
                    className="btn btn-secondary" 
                    style={{ padding: '8px 16px', fontSize: '0.8rem' }}
                  >
                    <Bookmark size={14} /> Save Job
                  </button>
                )}
                {match.status === 'saved' && (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--success)', fontSize: '0.85rem', padding: '0 8px' }}>
                    <Check size={16} /> Saved
                  </span>
                )}
                <button 
                  onClick={() => onStatusUpdate(job.id, 'dismissed')}
                  className="btn btn-secondary" 
                  style={{ padding: '8px 16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}
                >
                  <Trash2 size={14} /> Dismiss
                </button>
              </div>

              <a 
                href={job.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary" 
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                Apply Now <ExternalLink size={14} />
              </a>
            </div>

          </div>
        )
      })}
    </div>
  )
}
