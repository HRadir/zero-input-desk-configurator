import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

export default function DebugPanel() {
  const { data, loading, error } = useCatalogueStore()
  const config = useConfigStore((s) => s.config)
  const hauteurMode = useConfigStore((s) => s.hauteurMode)
  const setConfig = useConfigStore((s) => s.setConfig)
  const setHauteurMode = useConfigStore((s) => s.setHauteurMode)

  if (loading) return <p className="debug-panel">Chargement du catalogue…</p>
  if (error) return <p className="debug-panel debug-error">Erreur catalogue : {error}</p>

  const plateau = data.plateaux.find((p) => p.id === config.plateauId)

  const toggleAccessoire = (id) => {
    const has = config.accessoires.includes(id)
    setConfig({
      accessoires: has ? config.accessoires.filter((a) => a !== id) : [...config.accessoires, id],
    })
  }

  return (
    <div className="debug-panel">
      <h3>Debug — config manuelle</h3>

      <label>
        Finition
        <select
          data-testid="select-finition"
          value={config.finitionId}
          onChange={(e) => setConfig({ finitionId: e.target.value })}
        >
          {data.finitions.map((f) => (
            <option key={f.id} value={f.id}>
              {f.nom}
            </option>
          ))}
        </select>
      </label>

      <label>
        Plateau
        <select
          value={config.plateauId}
          onChange={(e) => {
            const newPlateau = data.plateaux.find((p) => p.id === e.target.value)
            setConfig({ plateauId: e.target.value, largeurChoisieCm: newPlateau.largeurs_disponibles_cm[0] })
          }}
        >
          {data.plateaux.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nom}
            </option>
          ))}
        </select>
      </label>

      <label>
        Largeur
        <select
          value={config.largeurChoisieCm}
          onChange={(e) => setConfig({ largeurChoisieCm: Number(e.target.value) })}
        >
          {plateau?.largeurs_disponibles_cm.map((l) => (
            <option key={l} value={l}>
              {l} cm
            </option>
          ))}
        </select>
      </label>

      <label>
        Structure
        <select value={config.structureId} onChange={(e) => setConfig({ structureId: e.target.value })}>
          {data.structures.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nom}
            </option>
          ))}
        </select>
      </label>

      <label>
        Nombre d'écrans
        <select
          value={config.nombreEcrans}
          onChange={(e) => setConfig({ nombreEcrans: Number(e.target.value) })}
        >
          {[1, 2, 3].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>

      <fieldset>
        <legend>Accessoires</legend>
        {data.accessoires.map((a) => (
          <label key={a.id} className="checkbox-row">
            <input
              type="checkbox"
              checked={config.accessoires.includes(a.id)}
              onChange={() => toggleAccessoire(a.id)}
            />
            {a.nom}
          </label>
        ))}
      </fieldset>

      <label>
        Hauteur (démo 3D)
        <select data-testid="select-hauteur" value={hauteurMode} onChange={(e) => setHauteurMode(e.target.value)}>
          <option value="assis">Assis</option>
          <option value="debout">Debout</option>
        </select>
      </label>
    </div>
  )
}
