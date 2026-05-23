import React, { useState, useEffect } from 'react'
import { Search, Sparkles, Bookmark, Briefcase, RefreshCw } from 'lucide-react'
import JobList, { Match } from './JobList'

interface DashboardProps {
  token: string
  API_BASE: string
}

export default function Dashboard({ token, API_BASE }: DashboardProps) {
  const [matches, setMatches] = useState<Match[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [activeSubTab, setActiveSubTab] = useState<'pending' | 'saved'>('pending')
  const [loading, setLoading] = useState(false)
  const [crawling, setCrawling] = useState(false)
  
  // Stat metrics
  const [totalMatches, setTotalMatches] = useState(0)
  const [avgScore, setAvgScore] = useState(0)
  const [totalSaved, setTotalSaved] = useState(0)

  useEffect(() => {
    fetchMatches()
  }, [activeSubTab])

  const fetchMatches = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/matches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data: Match[] = await res.json()
        
        // Compute overall stats regardless of subtab
        setTotalMatches(data.length)
        setTotalSaved(data.filter(m => m.status === 'saved').length)
        if (data.length > 0) {
          const sum = data.reduce((acc, curr) => acc + curr.match_score, 0)
          setAvgScore(Math.round((sum / data.length) * 100))
        } else {
          setAvgScore(0)
        }

        // Filter based on currently active subtab
        if (activeSubTab === 'pending') {
          // Display jobs that are pending, viewed or saved (but not dismissed or applied)
          setMatches(data.filter(m => m.status !== 'dismissed' && m.status !== 'applied'))
        } else {
          setMatches(data.filter(m => m.status === 'saved'))
        }
      }
    } catch {
      console.error("Failed to fetch matches from PJSAP Gateway.")
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      fetchMatches()
      return
    }

    setLoading(true)
    try {
      // Query crawled job index directly
      const res = await fetch(`${API_BASE}/jobs?q=${searchQuery}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        
        // Wrap searched raw jobs in transient Match models so they render in JobList
        const transientMatches: Match[] = data.map((job: any) => ({
          job,
          // Since it's a direct keyword search query, we calculate a mock semantic match score
          match_score: 0.85,
          matching_details: {
            reasons: ["Matched via full-text keyword search index query."],
            matched_keywords: [searchQuery]
          },
          status: 'pending'
        }))
        setMatches(transientMatches)
      }
    } catch {
      console.error("Fuzzy full-text search failed.")
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (jobId: string, newStatus: string) => {
    try {
      const res = await fetch(`${API_BASE}/matches/${jobId}/status`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      })
      if (res.ok) {
        // Refresh feed data
        fetchMatches()
      }
    } catch {
      console.error("Failed to update match status.")
    }
  }

  const triggerManualCrawlerDemo = async () => {
    setCrawling(true)
    try {
      const crawlQuery = searchQuery.trim() || 'Python'
      const res = await fetch(`${API_BASE}/jobs/crawl?query=${encodeURIComponent(crawlQuery)}`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (res.ok) {
        const result = await res.json()
        await fetchMatches()
        
        if (result.mode === 'standalone_sync' && result.details) {
          const stats = result.details
          alert(
            `🚀 Real-time Crawl & Match Completed!\n` +
            `-----------------------------------\n` +
            `• Target Keyword: "${crawlQuery}"\n` +
            `• Total Crawled (LinkedIn/Indeed/Glassdoor/StackOverflow/GitHub): ${stats.jobs_crawled_count}\n` +
            `• New Deduplicated Jobs Saved: ${stats.new_jobs_saved}\n` +
            `• Matches Generated (Similarity ≥ 30%): ${stats.matches_generated}\n` +
            `• Execution Mode: Standalone Developer Mode`
          )
        } else {
          alert(`✅ Crawler task for "${crawlQuery}" successfully dispatched to Celery background workers. Refresh the feed in a few moments!`)
        }
      } else {
        alert("Crawler trigger request returned a non-ok server response.")
      }
    } catch {
      alert("Cannot connect to backend server crawling endpoint. Verify the API is online.")
    } finally {
      setCrawling(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* 3 STATS CARDS ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
        
        {/* Metric 1 */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div className="brand-gradient" style={{ width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 10px var(--primary-glow)' }}>
            <Briefcase size={20} color="white" />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Discovered Matches</span>
            <span style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>{totalMatches}</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--accent)', backgroundColor: 'rgba(6, 182, 212, 0.1)' }}>
            <Sparkles size={20} color="var(--accent)" />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Avg Match Relevancy</span>
            <span style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--accent)' }}>{avgScore}%</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--success)', backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
            <Bookmark size={20} color="var(--success)" />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Saved Listings</span>
            <span style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--success)' }}>{totalSaved}</span>
          </div>
        </div>

      </div>

      {/* FILTER & CRAWL ACTIONS HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Feed Filtering Tabs */}
        <div style={{ display: 'flex', gap: '8px', backgroundColor: 'var(--bg-secondary)', padding: '6px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
          <button 
            onClick={() => setActiveSubTab('pending')}
            className={`btn ${activeSubTab === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 16px', fontSize: '0.8rem', border: 'none' }}
          >
            Best Matches
          </button>
          <button 
            onClick={() => setActiveSubTab('saved')}
            className={`btn ${activeSubTab === 'saved' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 16px', fontSize: '0.8rem', border: 'none' }}
          >
            Saved Feed
          </button>
        </div>

        {/* Manual Crawler Action */}
        <button onClick={triggerManualCrawlerDemo} className="btn btn-secondary" disabled={crawling} style={{ fontSize: '0.85rem' }}>
          {crawling ? (
            <><RefreshCw size={14} className="animate-spin" /> Fetching Jobs...</>
          ) : (
            <><RefreshCw size={14} /> Refresh Feeds & Run Matcher</>
          )}
        </button>
      </div>

      {/* ACTIVE SEARCH BAR */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
            placeholder="Fuzzy full-text search Elasticsearch index (e.g. Python DevOps Kubernetes)..." 
            style={{ paddingLeft: '44px', paddingRight: '16px' }}
          />
        </div>
        <button type="submit" className="btn btn-primary" style={{ padding: '0 24px' }}>
          Search
        </button>
      </form>

      {/* MATCHED JOB LIST */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
          <RefreshCw size={24} className="animate-spin" style={{ marginBottom: '12px', color: 'var(--primary)' }} />
          <p style={{ fontSize: '0.9rem' }}>Matching vectors aligning. Analyzing postings...</p>
        </div>
      ) : (
        <JobList matches={matches} onStatusUpdate={handleStatusUpdate} />
      )}

    </div>
  )
}
