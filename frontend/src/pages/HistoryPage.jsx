import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Film, ChevronRight, Clock, CheckCircle, XCircle, Loader } from 'lucide-react'
import './HistoryPage.css'

function StatusIcon({ status }) {
  if (status === 'done') return <CheckCircle size={16} color="var(--green)" />
  if (status === 'error') return <XCircle size={16} color="#f87171" />
  return <Loader size={16} color="var(--yellow)" className="spin" />
}

export default function HistoryPage() {
  const [jobs, setJobs] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    const load = () =>
      fetch('/api/jobs')
        .then(r => r.json())
        .then(data => setJobs(data.slice().reverse()))
        .catch(() => {})

    load()
    const id = setInterval(load, 3000)
    return () => clearInterval(id)
  }, [])

  if (jobs.length === 0) {
    return (
      <div>
        <h1 className="page-title">History</h1>
        <p className="page-subtitle">All your processed videos appear here.</p>
        <div className="empty-history">
          <Film size={40} color="var(--border)" />
          <p>No videos yet. Upload one to get started.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">History</h1>
      <p className="page-subtitle">{jobs.length} video{jobs.length !== 1 ? 's' : ''} processed this session.</p>

      <div className="history-list">
        {jobs.map(job => (
          <button
            key={job.id}
            className="history-item card"
            onClick={() => navigate(`/job/${job.id}`)}
          >
            <div className="history-icon">
              <Film size={20} />
            </div>
            <div className="history-body">
              <span className="history-name">{job.filename}</span>
              <span className="history-meta">
                <Clock size={12} /> {new Date(job.created_at).toLocaleString()}
                {job.status === 'done' && ` · ${job.clips.length} Short${job.clips.length !== 1 ? 's' : ''}`}
              </span>
              {(job.status === 'processing' || job.status === 'queued') && (
                <div className="history-progress">
                  <div className="progress-bar" style={{ width: 200 }}>
                    <div className="progress-fill" style={{ width: `${job.progress}%` }} />
                  </div>
                  <span>{job.progress}%</span>
                </div>
              )}
            </div>
            <div className="history-right">
              <StatusIcon status={job.status} />
              <ChevronRight size={16} color="var(--text2)" />
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
