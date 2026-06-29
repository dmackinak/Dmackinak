import { useState, useEffect } from 'react'
import { Save, CheckCircle } from 'lucide-react'
import './SettingsPage.css'

const POSITIONS = [
  { value: 'bottom-right', label: 'Bottom right' },
  { value: 'bottom-left', label: 'Bottom left' },
  { value: 'bottom-center', label: 'Bottom center' },
  { value: 'top-right', label: 'Top right' },
  { value: 'top-left', label: 'Top left' },
  { value: 'top-center', label: 'Top center' },
]

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/settings')
      .then(r => r.json())
      .then(setSettings)
      .catch(() => setError('Could not load settings.'))
  }, [])

  const set = (key, value) => setSettings(s => ({ ...s, [key]: value }))

  const save = async () => {
    setError('')
    try {
      const res = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      })
      if (!res.ok) throw new Error(await res.text())
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setError(`Save failed: ${e.message}`)
    }
  }

  if (!settings) return <div className="loading">Loading settings…</div>

  return (
    <div>
      <h1 className="page-title">Settings</h1>
      <p className="page-subtitle">These apply to every Short you generate — set your branding once and forget it.</p>

      {error && <div className="settings-error">{error}</div>}

      <div className="settings-sections">
        {/* Branding */}
        <section className="card settings-card">
          <h2 className="settings-section-title">Channel Branding</h2>
          <p className="settings-section-sub">Burned into every Short automatically.</p>

          <div className="field">
            <label>Channel name / watermark text</label>
            <input
              type="text"
              value={settings.channel_name}
              placeholder="e.g. @YourChannel"
              onChange={e => set('channel_name', e.target.value)}
            />
            <span className="field-hint">Leave blank to skip the watermark.</span>
          </div>

          <div className="field-row">
            <div className="field">
              <label>Position</label>
              <select value={settings.watermark_position} onChange={e => set('watermark_position', e.target.value)}>
                {POSITIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>

            <div className="field">
              <label>Text color</label>
              <div className="color-row">
                <input
                  type="color"
                  value={settings.watermark_color}
                  onChange={e => set('watermark_color', e.target.value)}
                />
                <input
                  type="text"
                  value={settings.watermark_color}
                  onChange={e => set('watermark_color', e.target.value)}
                  maxLength={7}
                  style={{ width: 90 }}
                />
              </div>
            </div>

            <div className="field">
              <label>Font size (px)</label>
              <input
                type="number"
                min={12}
                max={72}
                value={settings.watermark_size}
                onChange={e => set('watermark_size', parseInt(e.target.value, 10) || 28)}
                style={{ width: 80 }}
              />
            </div>
          </div>
        </section>

        {/* Clip settings */}
        <section className="card settings-card">
          <h2 className="settings-section-title">Clip Settings</h2>
          <p className="settings-section-sub">How long and how many Shorts to generate.</p>

          <div className="field-row">
            <div className="field">
              <label>Min clip duration (seconds)</label>
              <input
                type="number"
                min={10}
                max={55}
                value={settings.short_duration_min}
                onChange={e => set('short_duration_min', parseInt(e.target.value, 10) || 20)}
                style={{ width: 80 }}
              />
            </div>
            <div className="field">
              <label>Max clip duration (seconds)</label>
              <input
                type="number"
                min={15}
                max={59}
                value={settings.short_duration_max}
                onChange={e => set('short_duration_max', parseInt(e.target.value, 10) || 55)}
                style={{ width: 80 }}
              />
            </div>
            <div className="field">
              <label>Max clips per video</label>
              <input
                type="number"
                min={1}
                max={10}
                value={settings.max_clips}
                onChange={e => set('max_clips', parseInt(e.target.value, 10) || 5)}
                style={{ width: 80 }}
              />
            </div>
          </div>
          <p className="field-hint" style={{ marginTop: 8 }}>YouTube Shorts must be under 60 seconds.</p>
        </section>
      </div>

      <div className="save-row">
        <button className="btn btn-primary" onClick={save}>
          {saved ? <><CheckCircle size={16} /> Saved!</> : <><Save size={16} /> Save settings</>}
        </button>
        {saved && <span className="saved-hint">Settings applied to all future uploads.</span>}
      </div>
    </div>
  )
}
