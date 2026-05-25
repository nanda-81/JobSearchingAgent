import React, { useState, useEffect } from 'react'
import { Search, Sparkles, Bookmark, Briefcase, RefreshCw, Download } from 'lucide-react'
import { motion } from 'framer-motion'
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
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    fetchMatches()
  }, [activeSubTab])

  const downloadSavedCSV = async () => {
    setDownloading(true)
    try {
      const res = await fetch(`${API_BASE}/matches/export-csv`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'pjsap_job_tracker.csv'
        document.body.appendChild(a)
        a.click()
        a.remove()
      } else {
        alert("⚠️ No saved job matches found to export yet.")
      }
    } catch {
      alert("⚠️ Error downloading spreadsheet.")
    } finally {
      setDownloading(false)
    }
  }

  const fetchMatches = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/matches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data: Match[] = await res.json()
        
        // Compute overall stats
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
      const res = await fetch(`${API_BASE}/jobs?q=${searchQuery}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        
        const transientMatches: Match[] = data.map((job: any) => ({
          job,
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
    <div className="space-y-10">
      
      {/* Dashboard Top Header Section */}
      <div>
        <h1 className="text-3xl font-extrabold font-display tracking-tight text-white mb-2">
          Agent <span className="text-accent-primary">Job Matches Console</span>
        </h1>
        <p className="text-slate-400 text-sm font-medium">
          Real-time semantic vector matching pipelines and automated target crawler statistics.
        </p>
      </div>

      {/* 3 Premium Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card 1: Matches Discovered */}
        <motion.div 
          whileHover={{ translateY: -3 }}
          className="glass-panel p-6 rounded-2xl flex items-center gap-5 border-l-4 border-l-accent-primary border-accent-glow"
        >
          <div className="p-3.5 bg-accent-primary/10 rounded-xl text-accent-primary shadow-glow-primary">
            <Briefcase className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Vector Matches
            </span>
            <span className="text-3xl font-extrabold font-display text-white">
              {totalMatches}
            </span>
          </div>
        </motion.div>

        {/* Card 2: Match Relevancy */}
        <motion.div 
          whileHover={{ translateY: -3 }}
          className="glass-panel p-6 rounded-2xl flex items-center gap-5 border-l-4 border-l-accent-primary border-accent-glow"
        >
          <div className="p-3.5 bg-accent-primary/10 rounded-xl text-accent-primary shadow-glow-primary">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Avg Relevancy
            </span>
            <span className="text-3xl font-extrabold font-display text-accent-primary">
              {avgScore}%
            </span>
          </div>
        </motion.div>

        {/* Card 3: Saved Listings */}
        <motion.div 
          whileHover={{ translateY: -3 }}
          className="glass-panel p-6 rounded-2xl flex items-center gap-5 border-l-4 border-l-success border-accent-glow"
        >
          <div className="p-3.5 bg-success/10 rounded-xl text-success shadow-glow-success">
            <Bookmark className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Saved Tracker
            </span>
            <span className="text-3xl font-extrabold font-display text-success">
              {totalSaved}
            </span>
          </div>
        </motion.div>
      </div>

      {/* FILTER & CRAWL ACTIONS HEADER */}
      <div className="flex justify-between items-center flex-wrap gap-4 border-t border-slate-800/80 pt-8">
        
        {/* Custom Segmented Switch tabs */}
        <div className="flex bg-slate-900 border border-slate-850 p-1.5 rounded-xl">
          <button 
            onClick={() => setActiveSubTab('pending')}
            className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all duration-300 ${
              activeSubTab === 'pending'
                ? 'bg-accent-primary text-white shadow-glow-primary'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Best Matches
          </button>
          <button 
            onClick={() => setActiveSubTab('saved')}
            className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all duration-300 ${
              activeSubTab === 'saved'
                ? 'bg-accent-primary text-white shadow-glow-primary'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Saved Feed
          </button>
        </div>

        {/* Actions Button panel */}
        <div className="flex gap-3 items-center">
          {activeSubTab === 'saved' && (
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={downloadSavedCSV} 
              className="px-5 py-2.5 bg-slate-900 hover:bg-success/5 text-success hover:border-success/35 border border-slate-800 text-xs font-bold uppercase tracking-wider rounded-xl transition-all duration-300 flex items-center gap-2"
              disabled={downloading}
            >
              <Download className="h-4 w-4" />
              <span>{downloading ? 'Exporting...' : 'Export Spreadsheet'}</span>
            </motion.button>
          )}

          {/* Crawler Dispatch Button */}
          <motion.button 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={triggerManualCrawlerDemo} 
            className="px-5 py-2.5 bg-accent-primary hover:bg-accent-primary/95 text-white shadow-glow-primary text-xs font-bold uppercase tracking-wider rounded-xl transition-all duration-300 flex items-center gap-2"
            disabled={crawling}
          >
            {crawling ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                <span>Dispatch Match Worker</span>
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Commands / Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input 
            type="text" 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
            placeholder="Type job queries (e.g. Python DevOps Kubernetes) to scan vectors..." 
            className="w-full pl-12 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all duration-300 text-sm font-medium"
          />
        </div>
        <motion.button 
          whileTap={{ scale: 0.98 }}
          type="submit" 
          className="px-6 bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300"
        >
          Search
        </motion.button>
      </form>

      {/* Matched Feed listings display */}
      <div className="pt-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <RefreshCw className="h-8 w-8 animate-spin text-accent-primary mb-4" />
            <p className="text-sm font-semibold tracking-wider uppercase text-slate-500">
              Aligning semantic clusters...
            </p>
          </div>
        ) : (
          <JobList matches={matches} onStatusUpdate={handleStatusUpdate} token={token} API_BASE={API_BASE} />
        )}
      </div>

    </div>
  )
}
