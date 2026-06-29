import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, CheckCircle, XCircle, Loader, Clock } from 'lucide-react'
import './JobPage.css'

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function StatusBadge({ status }) {
  if (status === 'done') return <span className="badge badge-green"><CheckCircle size={12} /> Done</span>
  if (status === 'error') return <span className="badge badge-red"><XCircle size={12} /> Error</span>
  if (status === 'processing') return <span className="badge badge-yellow"><Loader size={12} className="spin" /> Processing</span>
  return <span className="badge badge-gray"><Clock size={12} /> Queued</span>
}

export default function JobPage() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let interval
    const poll = async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`)
        if (!res.ok) throw new Error('Job not found')
        const data = await res.json()
        setJob(data)
        if (data.status === 'done' || data.status === 'error') {
          clearInterval(interval)
        }
      } catch (e) {
        setError(e.message)
        clearInterval(interval)
      }
    }
    poll()
    interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [jobId])

  const downloadClip = (clip) => {
    const a = document.createElement('a')
    a.href = `/api/clips/${jobId}/${clip.filename}`
    a.download = clip.filename
    a.click()
  }

  const downloadAll = () => {
    job.clips.forEach((c, i) => {
      setTimeout(() => downloadClip(c), i * 400)
    })
  }

  if (error) return (
    <div>
      <button className="btn btn-secondary back-btn" onClick={() => navigate('/')}>
        <ArrowLeft size={16} /> Back
      </button>
      <div className="job-error">{error}</div>
    </div>
  )

  if (!job) return <div className="loading-screen"><Loader size={24} className="spin" /> Loading…</div>

  return (
    <div>
      <button className="btn btn-secondary back-btn" onClick={() => navigate('/')}>
        <ArrowLeft size={16} /> New video
      </button>

      <div className="job-header">
        <div>
          <h1 className="page-title">{job.filename}</h1>
          <p className="page-subtitle">Job {job.id.slice(0, 8)}… · {new Date(job.created_at).toLocaleString()}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {(job.status === 'processing' || job.status === 'queued') && (
        <div className="progress-card card">
          <div className="progress-label">
            <span>{job.message}</span>
            <span>{job.progress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${job.progress}%` }} />
          </div>
          <p className="progress-hint">
            First run downloads the Whisper model (~75 MB) — takes a few minutes. Subsequent runs are faster.
          </p>
        </div>
      )}

      {job.status === 'error' && (
        <div className="error-card card">
          <XCircle size={20} color="#f87171" />
          <div>
            <strong>Processing failed</strong>
            <p>{job.error}</p>
          </div>
        </div>
      )}

      {job.status === 'done' && job.clips.length > 0 && (
        <>
          <div className="clips-header">
            <h2 className="clips-title">{job.clips.length} Short{job.clips.length > 1 ? 's' : ''} ready</h2>
            <button className="btn btn-secondary" onClick={downloadAll}>
              <Download size={16} /> Download all
            </button>
          </div>

          {!job.clips[0].has_transcript && (
            <div className="notice-card">
              ⚠️ No transcript detected — clips were selected by even spacing. Install <code>faster-whisper</code> for smarter selection.
            </div>
          )}

          <div className="clips-grid">
            {job.clips.map((clip, i) => (
              <div key={clip.id} className="clip-card card">
                <div className="clip-video-wrap">
                  <video
                    src={`/api/clips/${jobId}/${clip.filename}`}
                    controls
                    preload="metadata"
                    className="clip-video"
                  />
                </div>
                <div className="clip-body">
                  <div className="clip-meta">
                    <span className="clip-num">Short #{i + 1}</span>
                    <span className="clip-time">
                      {formatTime(clip.start)} → {formatTime(clip.end)} · {clip.duration}s
                    </span>
                    {clip.score > 0 && (
                      <span className="clip-score">Score: {clip.score.toFixed(1)}</span>
                    )}
                  </div>
                  {clip.highlight && (
                    <p className="clip-highlight">"{clip.highlight}"</p>
                  )}
                  <button
                    className="btn btn-primary clip-dl-btn"
                    onClick={() => downloadClip(clip)}
                  >
                    <Download size={15} /> Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {job.status === 'done' && job.clips.length === 0 && (
        <div className="empty-card card">
          No clips could be extracted. Try adjusting duration settings.
        </div>
      )}
    </div>
  )
}
