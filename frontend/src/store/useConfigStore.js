import { create } from 'zustand'

const defaultConfig = {
  finitionId: 'finition_chene_clair',
  plateauId: 'plateau_standard',
  largeurChoisieCm: 140,
  structureId: 'structure_double_moteur',
  nombreEcrans: 1,
  accessoires: [],
  styleDemande: null,
}

export const useConfigStore = create((set) => ({
  config: defaultConfig,
  // hauteurMode pilote uniquement la démo visuelle assis/debout du viewer 3D,
  // ce n'est pas un champ du DeskConfig métier (cf. MODEL_NOTES.md : pas de rig dans le GLB source).
  hauteurMode: 'assis',
  setConfig: (partial) => set((state) => ({ config: { ...state.config, ...partial } })),
  setHauteurMode: (hauteurMode) => set({ hauteurMode }),
}))
