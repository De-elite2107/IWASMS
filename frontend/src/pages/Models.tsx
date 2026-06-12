import NavBar from '../components/NavBar'
import ModelPerformancePanel from '../components/ModelPerformancePanel'

export default function Models() {
  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0D1117',
        overflow: 'hidden',
      }}
    >
      <NavBar />
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '24px',
          maxWidth: '1100px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        <ModelPerformancePanel />
      </div>
    </div>
  )
}
