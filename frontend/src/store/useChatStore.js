import { create } from 'zustand'
import { useConfigStore } from './useConfigStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function backendConfigToStoreConfig(config) {
  return {
    finitionId: config.finition_id,
    plateauId: config.plateau_id,
    largeurChoisieCm: config.largeur_choisie_cm,
    structureId: config.structure_id,
    nombreEcrans: config.nombre_ecrans,
    accessoires: config.accessoires,
    styleDemande: config.style_demande,
  }
}

function storeConfigToBackendConfig(config) {
  return {
    finition_id: config.finitionId,
    plateau_id: config.plateauId,
    largeur_choisie_cm: config.largeurChoisieCm,
    structure_id: config.structureId,
    nombre_ecrans: config.nombreEcrans,
    accessoires: config.accessoires,
    style_demande: config.styleDemande,
  }
}

export const useChatStore = create((set, get) => ({
  messages: [], // { role: 'user' | 'assistant', content: string }
  loading: false,
  error: null,
  lastValidation: null, // { valid, errors, warnings } du dernier tour
  finalized: false,

  sendMessage: async (text) => {
    const trimmed = text.trim()
    if (!trimmed) return

    const history = get().messages.map((m) => ({ role: m.role, content: m.content }))
    set((state) => ({
      messages: [...state.messages, { role: 'user', content: trimmed }],
      loading: true,
      error: null,
    }))

    try {
      const currentConfig = storeConfigToBackendConfig(useConfigStore.getState().config)
      const res = await fetch(`${API_URL}/chat/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history, current_config: currentConfig }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      useConfigStore.getState().setConfig(backendConfigToStoreConfig(data.config))

      const summary = data.validation.valid
        ? 'Configuration mise à jour.'
        : `Configuration mise à jour, mais des points restent à ajuster : ${data.validation.errors
            .map((e) => e.message)
            .join(' ')}`

      set((state) => ({
        messages: [...state.messages, { role: 'assistant', content: summary }],
        lastValidation: data.validation,
        loading: false,
      }))
    } catch (err) {
      set((state) => ({
        messages: [
          ...state.messages,
          { role: 'assistant', content: `Erreur : impossible de générer la configuration (${err.message}).` },
        ],
        error: err.message,
        loading: false,
      }))
    }
  },

  finalize: () => set({ finalized: true }),
  reset: () => set({ messages: [], loading: false, error: null, lastValidation: null, finalized: false }),
}))
