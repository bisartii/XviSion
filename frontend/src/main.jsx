import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity, AlertTriangle, Bell, Camera, ChevronDown, ChevronLeft, ChevronRight,
  CircleUserRound, Cpu, Database, Eye, Gauge, Grid2X2, History, LayoutDashboard,
  Maximize2, Menu, Monitor, MoreHorizontal, Play, Plus, Search, Settings, Shield,
  SlidersHorizontal, Sparkles, Target, Users, Video, Wifi, X, Zap, LogOut, Lock, Mail, User, ArrowRight
} from 'lucide-react'
import './styles.css'

const API = 'http://127.0.0.1:8001'

function getToken() {
  return localStorage.getItem('xvision_token')
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  return fetch(`${API}${path}`, { ...options, headers })
}


const nav = [
  ['Overview', LayoutDashboard],
  ['Live Monitor', Monitor],
  ['People', Users],
  ['Events', History],
  ['Alerts', Bell],
  ['Settings', Settings],
]

function Glass({ children, className='' }) {
  return <div className={`glass ${className}`}>{children}</div>
}

function Badge({ children, tone='green' }) {
  return <span className={`badge ${tone}`}><span className="dot" />{children}</span>
}

function Metric({ label, value, meta, icon: Icon }) {
  return (
    <Glass className="metric">
      <div className="metric-top"><span>{label}</span><Icon size={17}/></div>
      <div className="metric-value">{value}</div>
      <div className="metric-meta">{meta}</div>
    </Glass>
  )
}

function CameraScene() {
  return (
    <div className="camera-scene">
      <img
        src="http://127.0.0.1:8001/video"
        alt="XviSion Live Camera"
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          display: "block",
        }}
      />
    </div>
  )
}

function Overview({ stats, events = [], detections = [] }) {
  const recognizedPct = (stats.faces_detected + stats.unknown_today) > 0
    ? Math.round((stats.recognized_today / Math.max(stats.recognized_today + stats.unknown_today, 1)) * 100)
    : 0

  return <Page title="Overview" eyebrow="REAL-TIME VISUAL INTELLIGENCE">
    <div className="hero-grid">
      <Glass className="hero-panel">
        <div>
          <div className="eyebrow">COMMAND CENTER</div>
          <h1>Good evening, <span>Operator.</span></h1>
          <p>XviSion is actively processing live camera data.</p>
          <div className="hero-statuses">
            <Badge>{stats.camera_running ? 'AI ENGINE ONLINE' : 'CAMERA OFFLINE'}</Badge>
            <Badge>TRACKING ACTIVE</Badge>
            <Badge>DATABASE CONNECTED</Badge>
          </div>
        </div>
        <div className="orb"><div className="orb-core"><Sparkles size={30}/></div></div>
      </Glass>
    </div>

    <div className="metrics">
      <Metric label="Faces Detected" value={String(stats.faces_detected)} meta="currently visible" icon={Eye}/>
      <Metric label="Recognized Today" value={String(stats.recognized_today)} meta={`${recognizedPct}% of logged detections`} icon={Shield}/>
      <Metric label="Unknown Today" value={String(stats.unknown_today)} meta="security alerts" icon={Target}/>
      <Metric label="Active Tracks" value={String(stats.active_tracks).padStart(2,'0')} meta="currently visible" icon={Activity}/>
      <Metric label="Events Today" value={String(stats.events_today)} meta="recognized events" icon={History}/>
      <Metric label="Active Alerts" value={String(stats.active_alerts).padStart(2,'0')} meta={`${stats.alerts_today} alerts today`} icon={Bell}/>
    </div>

    <div className="two-col">
      <Glass>
        <SectionHead title="Live Activity" action="View all"/>
        <Timeline events={events}/>
      </Glass>
      <Glass>
        <SectionHead title="Active Tracks" action="Monitor"/>
        <TrackList detections={detections}/>
      </Glass>
    </div>

    <SystemHealth stats={stats}/>
  </Page>
}

function Timeline({ events = [] }) {
  return <div className="timeline">
    {events.slice(0,4).map((e,i)=><div className="timeline-row" key={e.id ?? i}>
      <div className="timeline-time">{e.time}</div>
      <div className="timeline-marker" />
      <div className="timeline-copy"><strong>{e.person} recognized</strong><span>Track ID {e.track_id} · {Math.round((e.confidence ?? 0) * 100)}% confidence</span></div>
    </div>)}
    {events.length === 0 && <div className="empty-state"><p>No recognition events yet.</p></div>}
  </div>
}

function TrackList({ detections = [] }) {
  return <div className="track-list">
    {detections.map(d=><Track key={d.track_id} name={d.name} id={d.track_id} confidence={`${Math.round((d.confidence ?? 0) * 100)}%`} initials={d.name === 'Unknown' ? '?' : d.name?.[0]?.toUpperCase()} unknown={d.name === 'Unknown'}/>)}
    {detections.length === 0 && <div className="empty-state"><p>No active tracks.</p></div>}
  </div>
}

function Track({name,id,confidence,initials,unknown=false}) {
  return <div className="track">
    <div className={`avatar ${unknown?'unknown':''}`}>{initials}</div>
    <div className="track-main"><strong>{name}</strong><span>ID {id}</span></div>
    <div className="track-score"><strong>{confidence}</strong><span>confidence</span></div>
  </div>
}

function LiveMonitor({ stats }) {
  const [selected, setSelected] = useState('Camera 01')
  return <Page title="Live Monitor" eyebrow="MISSION CONTROL">
    <div className="monitor-layout">
      <Glass className="camera-list">
        <SectionHead title="Cameras" action={<Plus size={15}/>}/>
        <button className="camera-item active">
          <div className="mini-camera"><Video size={15}/></div>
          <div><strong>Camera 01</strong><span>{stats.camera_running ? 'ONLINE' : 'OFFLINE'}</span></div>
          <span className={`camera-status ${stats.camera_running ? '' : 'off'}`}/>
        </button>
      </Glass>

      <Glass className="monitor-main">
        <div className="monitor-toolbar">
          <div><strong>{selected}</strong><Badge>{stats.camera_running ? 'ONLINE' : 'OFFLINE'}</Badge></div>
          <div className="toolbar-actions"><button><Maximize2 size={16}/></button><button><MoreHorizontal size={16}/></button></div>
        </div>
        <CameraScene/>
        <div className="telemetry">
          <span>FPS <b>{stats.fps}</b></span><span>FACES <b>{stats.faces_detected}</b></span><span>TRACKS <b>{stats.active_tracks}</b></span><span>REGISTERED <b>{stats.registered_people}</b></span>
        </div>
      </Glass>

      <Glass className="intelligence">
        <SectionHead title="Live Intelligence" action={<Zap size={16}/>}/>
        <TrackList detections={stats.detections || []}/>
        <div className="divider"/>
        <SectionHead title="Live Events"/>
        <Timeline events={stats.recent_events || []}/>
      </Glass>
    </div>
  </Page>
}

function People({ people = [], refreshPeople }) {
  const [showRegister, setShowRegister] = useState(false)
  const [search, setSearch] = useState('')
  const [deleting, setDeleting] = useState('')

  const filtered = people.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  async function removePerson(name) {
    if (!window.confirm(`Remove ${name} from the face database?`)) return
    setDeleting(name)
    try {
      const res = await fetch(`${API}/api/people/${encodeURIComponent(name)}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(await res.text())
      await refreshPeople()
    } catch (err) {
      alert(`Could not remove ${name}. Make sure the backend has the DELETE /api/people/{name} endpoint.`)
      console.error(err)
    } finally {
      setDeleting('')
    }
  }

  return <Page title="People" eyebrow="FACE RECOGNITION REGISTRY" action={<button className="primary" onClick={()=>setShowRegister(true)}><Plus size={16}/> Add Person</button>}>
    <Glass className="toolbar people-toolbar">
      <div className="search"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search people..."/></div>
      <span className="people-count">{filtered.length} registered</span>
    </Glass>

    <div className="people-grid">
      {filtered.map(p=><Glass className="person-card" key={p.name}>
        <div className="person-top">
          <div className="large-avatar">{p.name[0]?.toUpperCase()}</div>
          <button className="danger-icon" title={`Remove ${p.name}`} onClick={()=>removePerson(p.name)} disabled={deleting===p.name}>
            {deleting===p.name ? '…' : <X size={17}/>} 
          </button>
        </div>
        <h3>{p.name}</h3>
        <span className="muted">{p.embeddings ?? 0} embeddings</span>
        <div className="person-stats">
          <div><span>Embeddings</span><b>{p.embeddings ?? 0}</b></div>
          <div><span>Status</span><b>Registered</b></div>
        </div>
        <Badge>REGISTERED</Badge>
      </Glass>)}

      {filtered.length === 0 && <Glass className="empty-state"><Users size={28}/><h3>No people found</h3><p>Add a person to the face database.</p><button className="primary" onClick={()=>setShowRegister(true)}><Plus size={16}/> Add Person</button></Glass>}
    </div>

    {showRegister && <RegisterModal close={()=>setShowRegister(false)} refreshPeople={refreshPeople}/>} 
  </Page>
}

function RegisterModal({close, refreshPeople}) {
  const [name, setName] = useState('')
  const [count, setCount] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function savePerson() {
    if (!name.trim()) return setError('Enter a name.')
    if (count < 30) return setError('Capture all 30 embeddings first.')
    setSaving(true); setError('')
    try {
      const res = await fetch(`${API}/api/people/register`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: name.trim() })
      })
      if (!res.ok) throw new Error(await res.text())
      await refreshPeople()
      close()
    } catch (err) {
      setError('Registration endpoint is not connected yet. Add POST /api/people/register to the backend.')
      console.error(err)
    } finally { setSaving(false) }
  }

  return <div className="modal-backdrop" onClick={close}>
    <div className="modal glass" onClick={e=>e.stopPropagation()}>
      <div className="modal-head"><div><div className="eyebrow">FACE ENROLLMENT</div><h2>Add Person</h2></div><button onClick={close}><X/></button></div>
      <input className="modal-input" value={name} onChange={e=>setName(e.target.value)} placeholder="Person name" />
      <div className="enroll-layout">
        <CameraScene/>
        <div className="enroll-info">
          <div className="progress-ring"><span>{count}<small>/30</small></span></div>
          <h3>Capture face embeddings</h3>
          <p>Look at the camera and slowly move your face in different directions.</p>
          <button className="primary wide" disabled={count>=30} onClick={()=>setCount(c=>Math.min(30,c+1))}>{count>=30?'30 Captured':'Capture embedding'}</button>
          <div className="progress"><span style={{width:`${count/30*100}%`}}/></div>
          {count===30 && <button className="primary wide save-person" disabled={saving} onClick={savePerson}>{saving?'Saving...':'Save Person'}</button>}
          {error && <p className="form-error">{error}</p>}
        </div>
      </div>
    </div>
  </div>
}

function Events({ events = [] }) {
  const [search, setSearch] = useState('')

  const filtered = events.filter(e =>
    e.person.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Page title="Event History" eyebrow="RECOGNITION & DETECTION RECORDS">

      <Glass className="event-controls">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search people, track IDs..."
          />
        </div>

        {['Today', 'Person', 'Confidence', 'Unknown only'].map(x => (
          <button key={x}>
            {x}
            <ChevronDown size={14} />
          </button>
        ))}

        <button className="export">Export</button>
      </Glass>

      <Glass className="table-card">

        <table>

          <thead>
            <tr>
              <th>TIME</th>
              <th>PERSON</th>
              <th>TRACK ID</th>
              <th>CONFIDENCE</th>
              <th>EVENT</th>
              <th>CAMERA</th>
              <th>STATUS</th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((e, i) => (
              <tr key={i}>

                <td>{e.time}</td>

                <td>
                  <div className="table-person">
                    <span
                      className={`tiny-avatar ${
                        e.person === 'Unknown' ? 'unknown' : ''
                      }`}
                    >
                      {e.person[0]}
                    </span>

                    {e.person}
                  </div>
                </td>

                <td>#{e.track_id}</td>

                <td>
                  <b>{e.confidence}%</b>
                </td>

                <td>
                  {e.person === 'Unknown'
                    ? 'Detection'
                    : 'Recognition'}
                </td>

                <td>Camera 01</td>

                <td>
                  <span
                    className={`status-text ${
                      e.person === 'Unknown' ? 'warning' : ''
                    }`}
                  >
                    {e.person === 'Unknown'
                      ? 'Unverified'
                      : 'Verified'}
                  </span>
                </td>

              </tr>
            ))}
          </tbody>

        </table>

      </Glass>

    </Page>
  )
}

function Alerts({ alerts = [], refreshAlerts }) {
  const [filter, setFilter] = useState('All')
  const visible = alerts.filter(a => {
    if (filter === 'Unacknowledged') return !a.acknowledged
    if (filter === 'Critical') return a.severity === 'critical'
    if (filter === 'Warning') return a.severity === 'warning'
    if (filter === 'Info') return a.severity === 'info'
    return true
  })

  async function acknowledge(id) {
    try {
      const res = await apiFetch(`/api/alerts/${id}/acknowledge`, { method: 'PATCH' })
      if (!res.ok) throw new Error(await res.text())
      await refreshAlerts()
    } catch (err) {
      console.error('Acknowledge alert error:', err)
    }
  }

  const active = alerts.filter(a => !a.acknowledged).length

  return <Page title="Alert Center" eyebrow="UNKNOWN DETECTION & SYSTEM ALERTS">
    <div className="alert-summary">
      <Metric label="Active" value={String(active).padStart(2,'0')} meta="requires attention" icon={Bell}/>
      <Metric label="Today" value={String(alerts.length).padStart(2,'0')} meta="stored alerts" icon={History}/>
    </div>
    <div className="tabs">{['All','Critical','Warning','Info','Unacknowledged'].map(x => <button key={x} className={filter===x?'active':''} onClick={()=>setFilter(x)}>{x}</button>)}</div>
    <div className="alert-list">
      {visible.map(a => <Glass className={`alert-card ${a.severity}`} key={a.id}>
        <div className="alert-icon">{a.severity==='critical'?<AlertTriangle/>:<Bell/>}</div>
        <div className="alert-body">
          <div className="alert-title"><h3>{a.title}</h3><span>{a.time}</span></div>
          <p>Camera 01 · Track {a.track_id ?? '—'} · Confidence {a.confidence != null ? `${Math.round(a.confidence * 100)}%` : '—'}</p>
          <div>{!a.acknowledged && <button className="ghost" onClick={()=>acknowledge(a.id)}>Acknowledge</button>}{a.acknowledged && <span className="status-text">Acknowledged</span>}</div>
        </div>
      </Glass>)}
      {visible.length === 0 && <Glass className="empty-state"><Bell size={28}/><h3>No alerts</h3><p>Unknown detections and system alerts will appear here.</p></Glass>}
    </div>
  </Page>
}

function Cameras() {
  return <Page title="Cameras" eyebrow="CAMERA INFRASTRUCTURE">
    <div className="people-grid camera-grid">{['Camera 01','Camera 02','Camera 03'].map((c,i)=><Glass className="camera-card" key={c}><CameraScene compact/><div className="camera-card-body"><div><h3>{c}</h3><span>{i===1?'Lobby':'Main Entrance'}</span></div><Badge tone={i===1?'red':'green'}>{i===1?'OFFLINE':'ONLINE'}</Badge></div><div className="camera-metrics"><span>FPS <b>{i===1?'—':'30'}</b></span><span>Latency <b>{i===1?'—':'42ms'}</b></span><span>AI <b>{i===1?'OFF':'ACTIVE'}</b></span></div></Glass>)}</div>
  </Page>
}

function Analytics() {
  return <Page title="Analytics" eyebrow="VISUAL INTELLIGENCE INSIGHTS">
    <div className="date-tabs"><button className="active">Today</button><button>7 Days</button><button>30 Days</button><button>Custom</button></div>
    <div className="metrics"><Metric label="Total Events" value="1,284" meta="+14.2%" icon={History}/><Metric label="Recognized" value="942" meta="73.4%" icon={Shield}/><Metric label="Unknown" value="342" meta="26.6%" icon={Target}/><Metric label="Avg. Confidence" value="89.4%" meta="+2.1%" icon={Gauge}/></div>
    <div className="two-col analytics-grid">
      <Glass className="chart-card"><SectionHead title="Recognitions over time" action="Hourly"/><Chart/></Glass>
      <Glass className="chart-card"><SectionHead title="Recognized vs Unknown"/><Donut/></Glass>
      <Glass className="chart-card"><SectionHead title="Events by hour"/><Bars/></Glass>
      <Glass className="chart-card"><SectionHead title="System performance"/><Performance/></Glass>
    </div>
  </Page>
}

function Chart() {
  return <div className="chart"><svg viewBox="0 0 700 220" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#54d6ff" stopOpacity=".3"/><stop offset="1" stopColor="#54d6ff" stopOpacity="0"/></linearGradient></defs><path d="M0 180 C70 160 90 170 140 120 S220 145 270 90 S350 120 400 70 S470 95 520 52 S610 78 700 20 V220 H0Z" fill="url(#area)"/><path d="M0 180 C70 160 90 170 140 120 S220 145 270 90 S350 120 400 70 S470 95 520 52 S610 78 700 20" fill="none" stroke="#78ddff" strokeWidth="3"/></svg><div className="chart-labels"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div></div>
}
function Donut(){return <div className="donut-wrap"><div className="donut"><div><strong>73%</strong><span>recognized</span></div></div><div className="legend"><span><i className="cyan"/>Recognized <b>942</b></span><span><i className="violet"/>Unknown <b>342</b></span></div></div>}
function Bars(){return <div className="bars">{[40,55,32,70,82,60,88,68,44,76,90,72].map((h,i)=><span key={i} style={{height:`${h}%`}}/>)}</div>}
function Performance(){return <div className="perf"><div><span>GPU</span><b>42%</b><i><em style={{width:'42%'}}/></i></div><div><span>VRAM</span><b>2.1 / 4 GB</b><i><em style={{width:'52%'}}/></i></div><div><span>FPS</span><b>28</b><i><em style={{width:'93%'}}/></i></div><div><span>Latency</span><b>36ms</b><i><em style={{width:'28%'}}/></i></div></div>}

function SettingsPage({ stats }) {
  return <Page title="Settings" eyebrow="SYSTEM CONFIGURATION & AI ENGINE">
    <div className="settings-layout">
      <Glass className="settings-nav">{['General','Recognition','Tracking','Camera','Events','Notifications','System'].map((x,i)=><button className={i===0?'active':''} key={x}>{x}</button>)}</Glass>
      <div className="settings-content">
        <Glass><SectionHead title="Recognition" action="AI ENGINE"/><Setting label="Recognition threshold" desc="Higher values make recognition stricter." value="0.45" slider/><Setting label="Embedding database" desc="Registered identities and embeddings." value="CONNECTED" good/><Setting label="Registered people" desc="Current identities in the database." value={String(stats.registered_people)}/></Glass>
        <Glass><SectionHead title="Tracking" action="ByteTrack"/><Setting label="Tracking engine" desc="Real-time object association." value="ACTIVE" good/><Setting label="Track timeout" desc="How long an inactive track is retained." value="10s"/></Glass>
        <Glass><SectionHead title="System Health"/><div className="health-grid"><Health icon={Cpu} label="AI Engine" value="ONLINE"/><Health icon={Eye} label="Face Detection" value="SCRFD"/><Health icon={Shield} label="Recognition" value="ArcFace"/><Health icon={Activity} label="Tracking" value="ByteTrack"/><Health icon={Database} label="Database" value="SQLite"/><Health icon={Zap} label="GPU" value="RTX 3050"/></div></Glass>
        <Glass><SectionHead title="Future Modules"/><div className="future-grid">{['YOLO Object Detection','ANPR','Vehicle Detection','Virtual Fence','Suspicious Activity','Multi-Camera Tracking'].map(x=><div className="future" key={x}><Sparkles size={16}/><span>{x}</span><small>COMING SOON</small></div>)}</div></Glass>
      </div>
    </div>
  </Page>
}

function Setting({label,desc,value,slider,good}) { return <div className="setting"><div><b>{label}</b><span>{desc}</span></div><div className="setting-value">{slider?<><span>{value}</span><input type="range" min="0" max="1" step=".01" defaultValue=".45"/></>:<span className={good?'good':''}>{value}</span>}</div></div>}
function Health({icon:Icon,label,value}) { return <div className="health"><Icon size={18}/><span>{label}</span><b>{value}</b><i className="health-dot"/></div> }

function SystemHealth({ stats }){return <Glass className="system-health"><SectionHead title="System Health" action={stats.camera_running ? "LIVE" : "OFFLINE"}/><div className="health-row"><Health icon={Cpu} label="AI Engine" value={stats.camera_running ? "ONLINE" : "OFFLINE"}/><Health icon={Eye} label="Face Detection" value="SCRFD"/><Health icon={Shield} label="Recognition" value="ArcFace"/><Health icon={Activity} label="Tracking" value="ByteTrack"/><Health icon={Database} label="Database" value="SQLite"/><Health icon={Zap} label="GPU" value="RTX 3050"/></div></Glass>}

function SectionHead({title,action}){return <div className="section-head"><h2>{title}</h2>{action&&<button className="text-btn">{action}</button>}</div>}

function Page({title,eyebrow,action,children}) {
  return <main className="page"><div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1></div>{action}</div>{children}</main>
}
function AuthShell({ children }) {
  return <div className="auth-shell">
    <div className="auth-glow"/>
    <div className="auth-brand"><div className="brand-mark"><Sparkles size={18}/></div><strong>XviSion</strong></div>
    {children}
  </div>
}

function Login({ onLogin, goSignup }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ email: email.trim(), password })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Login failed')
      localStorage.setItem('xvision_token', data.token)
      localStorage.setItem('xvision_user', JSON.stringify(data.user))
      onLogin(data.user)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return <AuthShell><div className="auth-card glass">
    <div className="eyebrow">SECURE ACCESS</div><h1>Welcome back</h1><p className="auth-subtitle">Sign in to your XviSion command center.</p>
    <form onSubmit={submit}>
      <label>Email</label><div className="auth-input"><Mail size={17}/><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="operator@example.com" required/></div>
      <label>Password</label><div className="auth-input"><Lock size={17}/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter password" required/></div>
      {error && <div className="form-error">{error}</div>}
      <button className="primary auth-submit" disabled={loading}>{loading?'Signing in...':<>Sign in <ArrowRight size={16}/></>}</button>
    </form>
    <p className="auth-switch">Don't have an account? <button onClick={goSignup}>Create account</button></p>
  </div></AuthShell>
}

function Signup({ onSignup, goLogin }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault(); setError('')
    if (password !== confirm) return setError('Passwords do not match.')
    if (password.length < 6) return setError('Password must be at least 6 characters.')
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/auth/signup`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ name: name.trim(), email: email.trim(), password })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Sign up failed')
      localStorage.setItem('xvision_token', data.token)
      localStorage.setItem('xvision_user', JSON.stringify(data.user))
      onSignup(data.user)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return <AuthShell><div className="auth-card glass">
    <div className="eyebrow">OPERATOR REGISTRATION</div><h1>Create account</h1><p className="auth-subtitle">Create a local XviSion operator account.</p>
    <form onSubmit={submit}>
      <label>Name</label><div className="auth-input"><User size={17}/><input value={name} onChange={e=>setName(e.target.value)} placeholder="Operator name" required/></div>
      <label>Email</label><div className="auth-input"><Mail size={17}/><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="operator@example.com" required/></div>
      <label>Password</label><div className="auth-input"><Lock size={17}/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Minimum 6 characters" required/></div>
      <label>Confirm password</label><div className="auth-input"><Lock size={17}/><input type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} placeholder="Repeat password" required/></div>
      {error && <div className="form-error">{error}</div>}
      <button className="primary auth-submit" disabled={loading}>{loading?'Creating account':<>Create account <ArrowRight size={16}/></>}</button>
    </form>
    <p className="auth-switch">Already have an account? <button onClick={goLogin}>Sign in</button></p>
  </div></AuthShell>
}

function App() {
  const [authMode, setAuthMode] = useState('login')
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('xvision_user') || 'null') } catch { return null }
  })
  const [page, setPage] = useState('Overview')
  const [collapsed, setCollapsed] = useState(false)
  const [time, setTime] = useState(new Date())
  const [backendPeople, setBackendPeople] = useState([])
  const [backendEvents, setBackendEvents] = useState([])
  const [backendAlerts, setBackendAlerts] = useState([])
  const [dashboard, setDashboard] = useState({faces_detected:0, recognized_today:0, unknown_today:0, active_tracks:0, events_today:0, alerts_today:0, active_alerts:0, fps:0, detections:[], camera_running:false, registered_people:0, recent_events:[]})

  const refreshPeople = async () => {
    try { const res=await apiFetch('/api/people'); if(res.status===401) return logout(); if(!res.ok) throw new Error(await res.text()); setBackendPeople(await res.json()) }
    catch(err){ console.error('People API error:',err) }
  }
  const refreshEvents = async () => {
    try { const res=await apiFetch('/api/events'); if(res.status===401) return logout(); if(!res.ok) throw new Error(await res.text()); setBackendEvents(await res.json()) }
    catch(err){ console.error('Events API error:',err) }
  }
  const refreshDashboard = async () => {
    try { const res=await apiFetch('/api/dashboard'); if(res.status===401) return logout(); if(!res.ok) throw new Error(await res.text()); setDashboard(await res.json()) }
    catch(err){ console.error('Dashboard API error:',err) }
  }
  const refreshAlerts = async () => {
    try { const res=await apiFetch('/api/alerts'); if(res.status===401) return logout(); if(!res.ok) throw new Error(await res.text()); setBackendAlerts(await res.json()) }
    catch(err){ console.error('Alerts API error:',err) }
  }
  function logout(){ localStorage.removeItem('xvision_token'); localStorage.removeItem('xvision_user'); setUser(null); setAuthMode('login') }

  useEffect(()=>{
    const id=setInterval(()=>setTime(new Date()),1000)
    if(!user) return ()=>clearInterval(id)
    refreshPeople(); refreshEvents(); refreshAlerts(); refreshDashboard()
    const poll=setInterval(()=>{ refreshPeople(); refreshEvents(); refreshAlerts(); refreshDashboard() },1000)
    return ()=>{ clearInterval(id); clearInterval(poll) }
  },[user])

  if(!user) {
    if(authMode==='signup') return <Signup onSignup={setUser} goLogin={()=>setAuthMode('login')}/>
    return <Login onLogin={setUser} goSignup={()=>setAuthMode('signup')}/>
  }

  const content = {
    Overview: <Overview stats={dashboard} events={backendEvents} detections={dashboard.detections}/>,
    'Live Monitor': <LiveMonitor stats={dashboard}/>,
    People: <People people={backendPeople} refreshPeople={refreshPeople}/>,
    Events: <Events events={backendEvents}/>,
    Alerts: <Alerts alerts={backendAlerts} refreshAlerts={refreshAlerts}/>,
    Settings: <SettingsPage stats={dashboard}/>
  }[page]

  return <div className={`app ${collapsed?'collapsed':''}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={17}/></div><div><strong>XviSion</strong></div></div>
      <button className="collapse" onClick={()=>setCollapsed(!collapsed)}>{collapsed?<ChevronRight/>:<ChevronLeft/>}</button>
      <nav>{nav.map(([name,Icon])=><button className={page===name?'active':''} key={name} onClick={()=>setPage(name)}><Icon size={19}/><span>{name}</span></button>)}</nav>
      <div className="sidebar-bottom"><div className="system-pill"><span className="live-dot"/> <span>AI ENGINE ONLINE</span></div><div className="profile"><div className="avatar">{user.name?.[0]?.toUpperCase() || 'O'}</div><div><b>{user.name || 'Operator'}</b><span>{user.email}</span></div><button className="logout-btn" title="Logout" onClick={logout}><LogOut size={16}/></button></div></div>
    </aside>
    <div className="main">
      <header className="topbar"><div className="mobile-title"><Menu size={20}/><b>XviSion</b></div><div className="top-actions"><div className="top-status"><span className="live-dot"/> AI ENGINE <b>ONLINE</b></div></div></header>
      {content}
    </div>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
