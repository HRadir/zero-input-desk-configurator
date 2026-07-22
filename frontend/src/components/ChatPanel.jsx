import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../store/useChatStore'
import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

function summarizeConfig(config, catalogue) {
  if (!catalogue) return ''
  const finition = catalogue.finitions.find((f) => f.id === config.finitionId)
  const plateau = catalogue.plateaux.find((p) => p.id === config.plateauId)
  const structure = catalogue.structures.find((s) => s.id === config.structureId)
  const accessoiresNoms = config.accessoires
    .map((id) => catalogue.accessoires.find((a) => a.id === id)?.nom)
    .filter(Boolean)

  const parts = [
    plateau && `Plateau ${plateau.nom.toLowerCase()}`,
    finition && `finition ${finition.nom.toLowerCase()}`,
    structure && structure.nom.toLowerCase(),
    `${config.largeurChoisieCm} cm`,
    `${config.nombreEcrans} écran${config.nombreEcrans > 1 ? 's' : ''}`,
    accessoiresNoms.length > 0 && accessoiresNoms.join(', '),
  ].filter(Boolean)

  return parts.join(' — ')
}

export default function ChatPanel() {
  const messages = useChatStore((s) => s.messages)
  const loading = useChatStore((s) => s.loading)
  const lastValidation = useChatStore((s) => s.lastValidation)
  const finalized = useChatStore((s) => s.finalized)
  const sendMessage = useChatStore((s) => s.sendMessage)
  const finalize = useChatStore((s) => s.finalize)

  const config = useConfigStore((s) => s.config)
  const catalogue = useCatalogueStore((s) => s.data)

  const [input, setInput] = useState('')
  const listRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, loading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    sendMessage(input)
    setInput('')
  }

  return (
    <div className="chat-panel">
      <h3>Configurateur conversationnel</h3>

      {catalogue && <div className="chat-summary">{summarizeConfig(config, catalogue)}</div>}

      <div className="chat-messages" ref={listRef}>
        {messages.length === 0 && (
          <p className="chat-empty">
            Décris le bureau que tu souhaites (style, matériaux, nombre d'écrans…).
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-message-${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-message-assistant chat-loading">Génération en cours…</div>
        )}
      </div>

      {lastValidation && lastValidation.errors.length > 0 && (
        <div className="chat-errors">
          <strong>Non résolu après plusieurs tentatives :</strong>
          {lastValidation.errors.map((e, i) => (
            <p key={i}>✕ {e.message}</p>
          ))}
        </div>
      )}

      {lastValidation && lastValidation.warnings.length > 0 && (
        <div className="chat-warnings">
          {lastValidation.warnings.map((w, i) => (
            <p key={i}>⚠ {w.message}</p>
          ))}
        </div>
      )}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ex : bureau scandinave, plateau bois clair, 2 écrans"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Envoyer
        </button>
      </form>

      <button type="button" className="chat-finalize" onClick={finalize} disabled={messages.length === 0}>
        Valider la configuration
      </button>

      {finalized && (
        <div className="chat-final-recap">
          <strong>Configuration finale :</strong>
          <p>{summarizeConfig(config, catalogue)}</p>
        </div>
      )}
    </div>
  )
}
