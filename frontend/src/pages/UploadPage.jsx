import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, Film, AlertCircle } from 'lucide-react'
import './UploadPage.css'

const ACCEPTED = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/mpeg']
const MAX_SIZE_GB = 4

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`
}

export default function UploadPage() {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef()
  const navigate = useNavigate()

  const validate = (f) => {
    if (!ACCEPTED.includes(f.type) && !f.name.match(/\.(mp4|mov|avi|webm|mpeg|mpg)$/i)) {
      return 'Please upload a video file (MP4, MOV, AVI, WebM).'
    }
    if (f.size > MAX_SIZE_GB * 1024 ** 3) {
      return `File too large. Max size is ${MAX_SIZE_GB} GB.`
    }
    return ''
  }

  const pick = (f) => {
    const err = validate(f)
    if (err) { setError(err); setFile(null); return }
    setError('')
    setFile(f)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) pick(f)
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const upload = async () => {
    if (!file || uploading) return
    setUploading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const { job_id } = await res.json()
      navigate(`/job/${job_id}`)
    } catch (e) {
      setError(`Upload failed: ${e.message}`)
      setUploading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">Upload Video</h1>
      <p className="page-subtitle">
        Upload a 5–10 minute video and get AI-selected YouTube Shorts cut automatically.
      </p>

      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !file && inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          style={{ display: 'none' }}
          onChange={e => e.target.files[0] && pick(e.target.files[0])}
        />

        {file ? (
          <div className="file-preview">
            <Film size={40} color="var(--accent)" />
            <div className="file-info">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatBytes(file.size)}</span>
            </div>
            <button
              className="btn btn-secondary"
              style={{ marginTop: 8 }}
              onClick={e => { e.stopPropagation(); setFile(null) }}
            >
              Change file
            </button>
          </div>
        ) : (
          <div className="drop-prompt">
            <UploadCloud size={48} color="var(--text2)" />
            <p className="drop-text">Drag &amp; drop your video here</p>
            <p className="drop-sub">or click to browse</p>
            <p className="drop-hint">MP4, MOV, AVI, WebM · up to {MAX_SIZE_GB} GB</p>
          </div>
        )}
      </div>

      {error && (
        <div className="upload-error">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      <div className="upload-actions">
        <button
          className="btn btn-primary"
          disabled={!file || uploading}
          onClick={upload}
        >
          {uploading ? 'Uploading…' : 'Cut my Shorts ✂️'}
        </button>
      </div>

      <div className="info-grid">
        <div className="info-card">
          <span className="info-icon">🎙️</span>
          <strong>AI Transcription</strong>
          <p>Whisper transcribes your audio and identifies the most engaging moments.</p>
        </div>
        <div className="info-card">
          <span className="info-icon">✂️</span>
          <strong>Auto-Cut Shorts</strong>
          <p>Videos are cut to 9:16, cropped for vertical, and trimmed to under 60 s.</p>
        </div>
        <div className="info-card">
          <span className="info-icon">🏷️</span>
          <strong>Consistent Branding</strong>
          <p>Your channel name is burned in every time — set it once in Settings.</p>
        </div>
      </div>
    </div>
  )
}
