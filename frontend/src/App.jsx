import { useEffect } from 'react'
import DeskViewer from './components/DeskViewer'
import ChatPanel from './components/ChatPanel'
import ConfigToolbar from './components/ConfigToolbar'
import ErrorBoundary from './components/ErrorBoundary'
import { useCatalogueStore } from './store/useCatalogueStore'
import { useConfigStore } from './store/useConfigStore'
import './App.css'

function App() {
  const fetchCatalogue = useCatalogueStore((s) => s.fetchCatalogue)
  const hauteurMode = useConfigStore((s) => s.hauteurMode)
  const setHauteurMode = useConfigStore((s) => s.setHauteurMode)

  useEffect(() => {
    fetchCatalogue()
  }, [fetchCatalogue])

  return (
    <div className="app-layout">
      <div className="viewer-pane">
        <ErrorBoundary>
          <DeskViewer />
        </ErrorBoundary>

        <ConfigToolbar />

        <div className="height-toggle" role="group" aria-label="Hauteur du bureau">
          <button
            type="button"
            className={`height-btn ${hauteurMode === 'assis' ? 'height-btn-active' : ''}`}
            onClick={() => setHauteurMode('assis')}
          >
            Assis
          </button>
          <button
            type="button"
            className={`height-btn ${hauteurMode === 'debout' ? 'height-btn-active' : ''}`}
            onClick={() => setHauteurMode('debout')}
          >
            Debout
          </button>
        </div>
      </div>
      <aside className="chat-pane">
        <ChatPanel />
      </aside>
    </div>
  )
}

export default App
