import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Bounds, ContactShadows, Environment, OrbitControls, useGLTF } from '@react-three/drei'
import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

// Translation verticale approximative "debout" vs "assis", en unités du modèle.
// Le GLB source n'a ni rig ni animation (cf. MODEL_NOTES.md) : on simule le mouvement
// en déplaçant tout le bureau (et les écrans posés dessus) en bloc plutôt que de
// télescoper les pieds individuellement.
const STAND_OFFSET_Y = 0.12

// Largeur/profondeur de référence (= config par défaut) servant de base à la mise à
// l'échelle relative du mesh. Le GLB étant un mesh unique fusionné sans cotes réelles
// connues en cm (cf. MODEL_NOTES.md), on approxime la largeur/profondeur choisies par un
// facteur d'échelle relatif à cette référence plutôt qu'une conversion cm -> unités exacte.
const REFERENCE_LARGEUR_CM = 140
const REFERENCE_PROFONDEUR_CM = 70

// Placement des écrans (monitor.glb, cf. MODEL_NOTES.md) : le modèle est en unités réelles
// (mètres) alors que le bureau est en unités arbitraires — le facteur d'échelle et les
// positions ci-dessous sont donc calés empiriquement (par capture d'écran), pas calculés.
const MONITOR_SCALE = 0.45
const MONITOR_FOOT_OFFSET = 0.205 // décalage local (bas du pied) dans monitor.glb
const DESK_TOP_LOCAL_Y = 0.273 // haut du plateau dans desk.glb (bounding box)
const MONITOR_GROUND_CLEARANCE = 0.035 // marge de sécurité pour éviter que le pied ne s'enfonce dans le plateau
const MONITOR_Y_OFFSET = DESK_TOP_LOCAL_Y + MONITOR_FOOT_OFFSET * MONITOR_SCALE + MONITOR_GROUND_CLEARANCE
const MONITOR_Z_OFFSET = -0.15
const MONITOR_BASE_X_POSITIONS = {
  1: [0],
  2: [-0.22, 0.22],
  3: [-0.34, 0, 0.34],
}

function Desk({ tintColor, scaleX, scaleZ }) {
  const { scene } = useGLTF('/models/desk.glb')
  // clone(true) évite de muter le scene graph mis en cache par useGLTF (partagé entre instances/hot-reload).
  const clonedScene = useMemo(() => scene.clone(true), [scene])
  const groupRef = useRef(null)

  useEffect(() => {
    clonedScene.traverse((child) => {
      if (child.isMesh) {
        child.material = child.material.clone()
      }
    })
  }, [clonedScene])

  useEffect(() => {
    clonedScene.traverse((child) => {
      if (child.isMesh) {
        child.material.color.set(tintColor)
      }
    })
  }, [clonedScene, tintColor])

  useFrame((_, delta) => {
    if (!groupRef.current) return
    const t = Math.min(delta * 4, 1)
    const currentScale = groupRef.current.scale
    currentScale.x += (scaleX - currentScale.x) * t
    currentScale.z += (scaleZ - currentScale.z) * t
  })

  return (
    <group ref={groupRef}>
      <primitive object={clonedScene} />
    </group>
  )
}

function Monitors({ count, scaleX, scaleZ }) {
  const { scene } = useGLTF('/models/monitor.glb')
  // Jusqu'à 3 instances pré-clonées une seule fois (pas de re-clonage à chaque changement de nombre d'écrans).
  const clones = useMemo(() => Array.from({ length: 3 }, () => scene.clone(true)), [scene])

  const positionsX = (MONITOR_BASE_X_POSITIONS[count] ?? MONITOR_BASE_X_POSITIONS[1]).map((x) => x * scaleX)

  return (
    <group position={[0, MONITOR_Y_OFFSET, MONITOR_Z_OFFSET * scaleZ]}>
      {positionsX.map((x, i) => (
        <primitive key={i} object={clones[i]} position={[x, 0, 0]} scale={MONITOR_SCALE} />
      ))}
    </group>
  )
}

function DeskRig({ tintColor, standing, scaleX, scaleZ, nombreEcrans }) {
  const riderRef = useRef(null)

  useFrame((_, delta) => {
    if (!riderRef.current) return
    const target = standing ? STAND_OFFSET_Y : 0
    const current = riderRef.current.position.y
    riderRef.current.position.y = current + (target - current) * Math.min(delta * 4, 1)
  })

  return (
    <group ref={riderRef}>
      <Desk tintColor={tintColor} scaleX={scaleX} scaleZ={scaleZ} />
      <Monitors count={nombreEcrans} scaleX={scaleX} scaleZ={scaleZ} />
    </group>
  )
}

export default function DeskViewer() {
  const config = useConfigStore((s) => s.config)
  const hauteurMode = useConfigStore((s) => s.hauteurMode)
  const catalogue = useCatalogueStore((s) => s.data)

  const finition = catalogue?.finitions.find((f) => f.id === config.finitionId)
  const plateau = catalogue?.plateaux.find((p) => p.id === config.plateauId)
  const tintColor = finition?.couleur_hex ?? '#ffffff'
  const scaleX = config.largeurChoisieCm / REFERENCE_LARGEUR_CM
  const scaleZ = (plateau?.profondeur_cm ?? REFERENCE_PROFONDEUR_CM) / REFERENCE_PROFONDEUR_CM

  return (
    <Canvas shadows camera={{ fov: 45, position: [3, 2.2, 4] }}>
      <color attach="background" args={['#f2efe8']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 5, 2]} intensity={1.2} castShadow />
      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.8}>
          <DeskRig
            tintColor={tintColor}
            standing={hauteurMode === 'debout'}
            scaleX={scaleX}
            scaleZ={scaleZ}
            nombreEcrans={config.nombreEcrans}
          />
        </Bounds>
        <Environment preset="city" />
        <ContactShadows position={[0, -0.001, 0]} opacity={0.35} scale={10} blur={2.5} far={2} />
      </Suspense>
      <OrbitControls makeDefault />
    </Canvas>
  )
}

useGLTF.preload('/models/desk.glb')
useGLTF.preload('/models/monitor.glb')
