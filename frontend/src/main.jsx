import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity, AlertTriangle, Bell, Camera, ChevronDown, ChevronLeft, ChevronRight,
  CircleUserRound, Cpu, Database, Eye, Gauge, Grid2X2, History, LayoutDashboard,
  Maximize2, Menu, Monitor, MoreHorizontal, Play, Plus, Search, Settings, Shield,
  SlidersHorizontal, Sparkles, Target, Users, Video, Wifi, X, Zap
} from 'lucide-react'
import './styles.css'

const nav = [
  ['Overview', LayoutDashboard],
  ['Live Monitor', Monitor],
  ['People', Users],
  ['Events', History],
  ['Alerts', AlertTriangle],
  ['Cameras', Camera],
  ['Analytics', Activity],
  ['Settings', Settings],
]

const people = [
  { name: 'Dhruv', embeddings: 30, seen: '00:42', appearances: 124, confidence: 92, initials: 'D' },
  { name: 'Mumma', embeddings: 30, seen: '00:39', appearances: 98, confidence: 89, initials: 'M' },
]

const events = [
  { time: '00:42:17', person: 'Dhruv', id: '04', confidence: 92, type: 'Recognition', camera: 'Camera 01', status: 'Verified' },
  { time: '00:41:53', person: 'Mumma', id: '06', confidence: 89, type: 'Recognition', camera: 'Camera 01', status: 'Verified' },
  { time: '00:41:11', person: 'Unknown', id: '07', confidence: 61, type: 'Detection', camera: 'Camera 01', status: 'Unverified' },
  { time: '00:39:52', person: 'Dhruv', id: '03', confidence: 94, type: 'Recognition', camera: 'Camera 01', status: 'Verified' },
  { time: '00:38:20', person: 'Mumma', id: '02', confidence: 91, type: 'Recognition', camera: 'Camera 01', status: 'Verified' },
]

const alerts = [
  { severity: 'warning', title: 'Unknown person detected', camera: 'Camera 01', track: '07', time: '00:42:11', confidence: '61%' },
  { severity: 'info', title: 'AI engine heartbeat received', camera: 'System', track: '—', time: '00:41:58', confidence: '100%' },
  { severity: 'critical', title: 'Camera 02 disconnected', camera: 'Camera 02', track: '—', time: '00:39:52', confidence: '—' },
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
        alt="Terra Vision Live Camera"
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

function Overview() {
  return <Page title="Overview" eyebrow="REAL-TIME VISUAL INTELLIGENCE">
    <div className="hero-grid">
      <Glass className="hero-panel">
        <div>
          <div className="eyebrow">COMMAND CENTER</div>
          <h1>Good evening, <span>Operator.</span></h1>
          <p>Terra Vision is actively processing visual data.</p>
          <div className="hero-statuses">
            <Badge>AI ENGINE ONLINE</Badge>
            <Badge>TRACKING ACTIVE</Badge>
            <Badge>DATABASE CONNECTED</Badge>
          </div>
        </div>
        <div className="orb"><div className="orb-core"><Sparkles size={30}/></div></div>
      </Glass>
    </div>

    <div className="metrics">
      <Metric label="Faces Detected" value="128" meta="+12% today" icon={Eye}/>
      <Metric label="Recognized" value="94" meta="73.4% of detections" icon={Shield}/>
      <Metric label="Unknown" value="34" meta="8 in the last hour" icon={Target}/>
      <Metric label="Active Tracks" value="07" meta="3 currently visible" icon={Activity}/>
      <Metric label="Events Today" value="56" meta="+8 since morning" icon={History}/>
      <Metric label="Alerts" value="03" meta="1 requires attention" icon={Bell}/>
    </div>

    <div className="two-col">
      <Glass>
        <SectionHead title="Live Activity" action="View all"/>
        <Timeline />
      </Glass>
      <Glass>
        <SectionHead title="Active Tracks" action="Monitor"/>
        <TrackList />
      </Glass>
    </div>

    <SystemHealth />
  </Page>
}

function Timeline() {
  return <div className="timeline">
    {events.slice(0,4).map((e,i)=><div className="timeline-row" key={i}>
      <div className="timeline-time">{e.time}</div>
      <div className={`timeline-marker ${e.person==='Unknown'?'amber':''}`} />
      <div className="timeline-copy"><strong>{e.person} {e.person==='Unknown'?'detected':'recognized'}</strong><span>Track ID {e.id} · {e.confidence}% confidence</span></div>
    </div>)}
  </div>
}

function TrackList() {
  return <div className="track-list">
    <Track name="Dhruv" id="04" confidence="92%" initials="D"/>
    <Track name="Mumma" id="06" confidence="89%" initials="M"/>
    <Track name="Unknown" id="07" confidence="61%" initials="?" unknown/>
  </div>
}

function Track({name,id,confidence,initials,unknown=false}) {
  return <div className="track">
    <div className={`avatar ${unknown?'unknown':''}`}>{initials}</div>
    <div className="track-main"><strong>{name}</strong><span>ID {id}</span></div>
    <div className="track-score"><strong>{confidence}</strong><span>confidence</span></div>
  </div>
}

function LiveMonitor() {
  const [selected, setSelected] = useState('Camera 01')
  return <Page title="Live Monitor" eyebrow="MISSION CONTROL">
    <div className="monitor-layout">
      <Glass className="camera-list">
        <SectionHead title="Cameras" action={<Plus size={15}/>}/>
        {['Camera 01','Camera 02','Camera 03'].map((c,i)=><button key={c} className={`camera-item ${selected===c?'active':''}`} onClick={()=>setSelected(c)}>
          <div className="mini-camera"><Video size={15}/></div>
          <div><strong>{c}</strong><span>{i===1?'OFFLINE':'Main Entrance'}</span></div>
          <span className={`camera-status ${i===1?'off':''}`}/>
        </button>)}
      </Glass>

      <Glass className="monitor-main">
        <div className="monitor-toolbar">
          <div><strong>{selected}</strong><Badge>{selected==='Camera 02'?'OFFLINE':'ONLINE'}</Badge></div>
          <div className="toolbar-actions"><button><Maximize2 size={16}/></button><button><MoreHorizontal size={16}/></button></div>
        </div>
        <CameraScene/>
        <div className="telemetry">
          <span>FPS <b>28</b></span><span>LATENCY <b>36ms</b></span><span>GPU <b>42%</b></span><span>VRAM <b>2.1GB</b></span><span>FACES <b>03</b></span><span>TRACKS <b>03</b></span>
        </div>
      </Glass>

      <Glass className="intelligence">
        <SectionHead title="Live Intelligence" action={<Zap size={16}/>}/>
        <TrackList/>
        <div className="divider"/>
        <SectionHead title="Live Events"/>
        <Timeline/>
      </Glass>
    </div>
  </Page>
}

function People({ people = [] }) {
  const [showRegister, setShowRegister] = useState(false)
  return <Page title="People" eyebrow="FACE RECOGNITION REGISTRY" action={<button className="primary" onClick={()=>setShowRegister(true)}><Plus size={16}/> Register Person</button>}>
    <div className="toolbar glass">
      <div className="search"><Search size={16}/><input placeholder="Search registered people..."/></div>
      <button><SlidersHorizontal size={16}/> Filter</button>
    </div>
    <div className="people-grid">
      {people.map(p=><Glass className="person-card" key={p.name}>
        <div className="person-top"><div className="large-avatar">{p.name[0]}</div><button><MoreHorizontal size={18}/></button></div>
        <h3>{p.name}</h3><span className="muted">{p.embeddings} embeddings</span>
        <div className="person-stats">
  <div>
    <span>Embeddings</span>
    <b>{p.embeddings}</b>
  </div>

  <div>
    <span>Status</span>
    <b>Registered</b>
  </div>

  <div>
    <span>Database</span>
    <b>Active</b>
  </div>
</div>
        <Badge>REGISTERED</Badge>
      </Glass>)}
    </div>
    {showRegister && <RegisterModal close={()=>setShowRegister(false)}/>}
  </Page>
}

function RegisterModal({close}) {
  const [count,setCount] = useState(17)
  return <div className="modal-backdrop" onClick={close}>
    <div className="modal glass" onClick={e=>e.stopPropagation()}>
      <div className="modal-head"><div><div className="eyebrow">FACE ENROLLMENT</div><h2>Register Person</h2></div><button onClick={close}><X/></button></div>
      <div className="enroll-layout"><CameraScene compact/><div className="enroll-info"><div className="progress-ring"><span>{count}<small>/30</small></span></div><h3>Capture face embeddings</h3><p>Look toward the camera and move your face slightly left, right, up and down.</p><button className="primary wide" onClick={()=>setCount(Math.min(30,count+1))}>Capture embedding</button><div className="progress"><span style={{width:`${count/30*100}%`}}/></div></div></div>
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

function Alerts() {
  return <Page title="Alert Center" eyebrow="REAL-TIME SYSTEM & VISION ALERTS">
    <div className="alert-summary"><Metric label="Active" value="03" meta="requires attention" icon={Bell}/><Metric label="Today" value="12" meta="all severities" icon={History}/></div>
    <div className="tabs"><button className="active">All</button><button>Critical</button><button>Warning</button><button>Info</button><button>Unacknowledged</button></div>
    <div className="alert-list">{alerts.map((a,i)=><Glass className={`alert-card ${a.severity}`} key={i}><div className="alert-icon">{a.severity==='critical'?<AlertTriangle/>:<Bell/>}</div><div className="alert-body"><div className="alert-title"><h3>{a.title}</h3><span>{a.time}</span></div><p>{a.camera} · Track {a.track} · Confidence {a.confidence}</p><div><button className="ghost">View Event</button><button className="ghost">Acknowledge</button></div></div></Glass>)}</div>
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

function SettingsPage() {
  return <Page title="Settings" eyebrow="SYSTEM CONFIGURATION & AI ENGINE">
    <div className="settings-layout">
      <Glass className="settings-nav">{['General','Recognition','Tracking','Camera','Events','Notifications','System'].map((x,i)=><button className={i===0?'active':''} key={x}>{x}</button>)}</Glass>
      <div className="settings-content">
        <Glass><SectionHead title="Recognition" action="AI ENGINE"/><Setting label="Recognition threshold" desc="Higher values make recognition stricter." value="0.45" slider/><Setting label="Embedding database" desc="Registered identities and embeddings." value="CONNECTED" good/><Setting label="Registered people" desc="Current identities in the database." value="2"/></Glass>
        <Glass><SectionHead title="Tracking" action="ByteTrack"/><Setting label="Tracking engine" desc="Real-time object association." value="ACTIVE" good/><Setting label="Track timeout" desc="How long an inactive track is retained." value="10s"/></Glass>
        <Glass><SectionHead title="System Health"/><div className="health-grid"><Health icon={Cpu} label="AI Engine" value="ONLINE"/><Health icon={Eye} label="Face Detection" value="SCRFD"/><Health icon={Shield} label="Recognition" value="ArcFace"/><Health icon={Activity} label="Tracking" value="ByteTrack"/><Health icon={Database} label="Database" value="SQLite"/><Health icon={Zap} label="GPU" value="RTX 3050"/></div></Glass>
        <Glass><SectionHead title="Future Modules"/><div className="future-grid">{['YOLO Object Detection','ANPR','Vehicle Detection','Virtual Fence','Suspicious Activity','Multi-Camera Tracking'].map(x=><div className="future" key={x}><Sparkles size={16}/><span>{x}</span><small>COMING SOON</small></div>)}</div></Glass>
      </div>
    </div>
  </Page>
}

function Setting({label,desc,value,slider,good}) { return <div className="setting"><div><b>{label}</b><span>{desc}</span></div><div className="setting-value">{slider?<><span>{value}</span><input type="range" min="0" max="1" step=".01" defaultValue=".45"/></>:<span className={good?'good':''}>{value}</span>}</div></div>}
function Health({icon:Icon,label,value}) { return <div className="health"><Icon size={18}/><span>{label}</span><b>{value}</b><i className="health-dot"/></div> }

function SystemHealth(){return <Glass className="system-health"><SectionHead title="System Health" action="LIVE"/><div className="health-row"><Health icon={Cpu} label="AI Engine" value="ONLINE"/><Health icon={Eye} label="Face Detection" value="SCRFD"/><Health icon={Shield} label="Recognition" value="ArcFace"/><Health icon={Activity} label="Tracking" value="ByteTrack"/><Health icon={Database} label="Database" value="SQLite"/><Health icon={Zap} label="GPU" value="RTX 3050"/></div></Glass>}

function SectionHead({title,action}){return <div className="section-head"><h2>{title}</h2>{action&&<button className="text-btn">{action}</button>}</div>}

function Page({title,eyebrow,action,children}) {
  return <main className="page"><div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1></div>{action}</div>{children}</main>
}
function App() {
  const [page, setPage] = useState('Overview')
  const [collapsed, setCollapsed] = useState(false)
  const [time, setTime] = useState(new Date())

  const [backendPeople, setBackendPeople] = useState([])
  const [backendEvents, setBackendEvents] = useState([])
useEffect(() => {
  const id = setInterval(() => setTime(new Date()), 1000)

  fetch("http://127.0.0.1:8000/api/people")
    .then(res => res.json())
    .then(data => setBackendPeople(data))
    .catch(err => console.error("People API error:", err))

  fetch("http://127.0.0.1:8000/api/events")
    .then(res => res.json())
    .then(data => setBackendEvents(data))
    .catch(err => console.error("Events API error:", err))

  return () => clearInterval(id)
}, [])
  const content = useMemo(() => ({
  Overview: <Overview events={backendEvents} />,
  'Live Monitor': <LiveMonitor />,
  People: <People people={backendPeople} />,
  Events: <Events events={backendEvents} />,
  Alerts: <Alerts />,
  Cameras: <Cameras />,
  Analytics: <Analytics />,
  Settings: <SettingsPage />
}[page]), [page, backendPeople, backendEvents])
  return <div className={`app ${collapsed ? 'collapsed' : ''}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={17}/></div><div><strong>TERRA</strong><span>VISION</span></div></div>
      <button className="collapse" onClick={()=>setCollapsed(!collapsed)}>{collapsed?<ChevronRight/>:<ChevronLeft/>}</button>
      <nav>{nav.map(([name,Icon])=><button className={page===name?'active':''} key={name} onClick={()=>setPage(name)}><Icon size={19}/><span>{name}</span></button>)}</nav>
      <div className="sidebar-bottom"><div className="system-pill"><span className="live-dot"/> <span>AI ENGINE ONLINE</span></div><div className="profile"><div className="avatar">O</div><div><b>Operator</b><span>Command access</span></div></div></div>
    </aside>
    <div className="main">
      <header className="topbar"><div className="mobile-title"><Menu size={20}/><b>TERRA VISION</b></div><div className="top-search"><Search size={16}/><span>Search people, events, cameras...</span><kbd>⌘ K</kbd></div><div className="top-actions"><div className="top-status"><span className="live-dot"/> AI ENGINE <b>ONLINE</b></div><div className="top-status"><Wifi size={14}/> CAM 01 <b>ONLINE</b></div><button><Bell size={18}/></button><button><CircleUserRound size={19}/></button></div></header>
      {content}
    </div>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
