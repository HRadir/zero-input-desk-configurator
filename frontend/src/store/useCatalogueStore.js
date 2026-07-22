import { create } from 'zustand'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useCatalogueStore = create((set) => ({
  data: null,
  loading: true,
  error: null,
  fetchCatalogue: async () => {
    try {
      const res = await fetch(`${API_URL}/catalogue`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      set({ data, loading: false, error: null })
    } catch (err) {
      set({ error: err.message, loading: false })
    }
  },
}))
