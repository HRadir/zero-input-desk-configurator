import { useEffect } from 'react'
import DeskViewer from './components/DeskViewer'
import DebugPanel from './components/DebugPanel'
import { useCatalogueStore } from './store/useCatalogueStore'
import './App.css'

function App() {
  const fetchCatalogue = useCatalogueStore((s) => s.fetchCatalogue)

  useEffect(() => {
    fetchCatalogue()
  }, [fetchCatalogue])

  return (
    <div className="app-layout">
      <div className="viewer-pane">
        <DeskViewer />
      </div>
      <aside className="chat-pane">
        <DebugPanel />
        <p className="chat-placeholder">Le chat conversationnel arrivera en Phase 10.</p>
      </aside>
    </div>
  )
}

export default App
