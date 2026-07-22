import { useEffect } from 'react'
import DeskViewer from './components/DeskViewer'
import ChatPanel from './components/ChatPanel'
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
        <ChatPanel />
        <DebugPanel />
      </aside>
    </div>
  )
}

export default App
