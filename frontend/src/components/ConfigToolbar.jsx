import { useState } from 'react'
import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

const STYLE = 'style'
const COLOR = 'color'
const COMPONENTS = 'components'

export default function ConfigToolbar() {
  const { data, loading, error } = useCatalogueStore()
  const config = useConfigStore((s) => s.config)
  const setConfig = useConfigStore((s) => s.setConfig)

  const [openDropdown, setOpenDropdown] = useState(null)

  if (loading || error || !data) return null

  const plateau = data.plateaux.find((p) => p.id === config.plateauId)
  const finitionActuelle = data.finitions.find((f) => f.id === config.finitionId)
  const toggle = (name) => setOpenDropdown((cur) => (cur === name ? null : name))

  const toggleAccessoire = (id) => {
    const has = config.accessoires.includes(id)
    setConfig({
      accessoires: has ? config.accessoires.filter((a) => a !== id) : [...config.accessoires, id],
    })
  }

  return (
    <div className="config-toolbar">
      {openDropdown && <div className="toolbar-backdrop" onClick={() => setOpenDropdown(null)} />}

      <div className="toolbar-group">
        <div className="toolbar-item">
          <button type="button" className="toolbar-btn" onClick={() => toggle(STYLE)}>
            Style <span className="chevron">⌄</span>
          </button>
          {openDropdown === STYLE && (
            <div className="toolbar-dropdown">
              <span className="dropdown-label">Plateau</span>
              <div className="swatch-row">
                {data.plateaux.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`option-chip ${p.id === config.plateauId ? 'option-chip-active' : ''}`}
                    onClick={() => setConfig({ plateauId: p.id, largeurChoisieCm: p.largeurs_disponibles_cm[0] })}
                  >
                    {p.nom}
                  </button>
                ))}
              </div>

              <span className="dropdown-label">Largeur</span>
              <div className="swatch-row">
                {plateau?.largeurs_disponibles_cm.map((l) => (
                  <button
                    key={l}
                    type="button"
                    className={`option-chip ${l === config.largeurChoisieCm ? 'option-chip-active' : ''}`}
                    onClick={() => setConfig({ largeurChoisieCm: l })}
                  >
                    {l} cm
                  </button>
                ))}
              </div>

              <span className="dropdown-label">Structure</span>
              <div className="swatch-row">
                {data.structures.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={`option-chip ${s.id === config.structureId ? 'option-chip-active' : ''}`}
                    onClick={() => setConfig({ structureId: s.id })}
                  >
                    {s.nom}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="toolbar-item">
          <button type="button" className="toolbar-btn" onClick={() => toggle(COLOR)}>
            Couleur <span className="chevron">⌄</span>
          </button>
          {openDropdown === COLOR && (
            <div className="toolbar-dropdown">
              <span className="dropdown-label">Finition</span>
              <div className="color-swatch-row">
                {data.finitions.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    title={f.nom}
                    aria-label={f.nom}
                    className={`color-swatch ${f.id === config.finitionId ? 'color-swatch-active' : ''}`}
                    style={{ backgroundColor: f.couleur_hex }}
                    onClick={() => setConfig({ finitionId: f.id })}
                  />
                ))}
              </div>
              <p className="dropdown-hint">{finitionActuelle?.nom}</p>
            </div>
          )}
        </div>

        <div className="toolbar-item">
          <button type="button" className="toolbar-btn" onClick={() => toggle(COMPONENTS)}>
            Composants <span className="chevron">⌄</span>
          </button>
          {openDropdown === COMPONENTS && (
            <div className="toolbar-dropdown">
              <span className="dropdown-label">Écrans</span>
              <div className="swatch-row">
                {[1, 2, 3].map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={`option-chip ${n === config.nombreEcrans ? 'option-chip-active' : ''}`}
                    onClick={() => setConfig({ nombreEcrans: n })}
                  >
                    {n}
                  </button>
                ))}
              </div>

              <span className="dropdown-label">Accessoires</span>
              <div className="accessoire-list">
                {data.accessoires.map((a) => (
                  <label key={a.id} className="accessoire-row">
                    <input
                      type="checkbox"
                      checked={config.accessoires.includes(a.id)}
                      onChange={() => toggleAccessoire(a.id)}
                    />
                    {a.nom}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
