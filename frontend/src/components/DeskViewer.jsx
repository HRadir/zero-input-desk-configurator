import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Bounds, ContactShadows, Environment, OrbitControls, useGLTF } from '@react-three/drei'
import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

// Translation verticale approximative "debout" vs "assis", en unités du modèle.
// Le GLB source n'a ni rig ni animation (cf. MODEL_NOTES.md) : on simule le mouvement
// en déplaçant tout le bureau en bloc plutôt que de télescoper les pieds individuellement.
const STAND_OFFSET_Y = 0.12

// Largeur/profondeur de référence (= config par défaut) servant de base à la mise à
// l'échelle relative du mesh. Le GLB étant un mesh unique fusionné sans cotes réelles
// connues en cm (cf. MODEL_NOTES.md), on approxime la largeur/profondeur choisies par un
// facteur d'échelle relatif à cette référence plutôt qu'une conversion cm -> unités exacte.
const REFERENCE_LARGEUR_CM = 140
const REFERENCE_PROFONDEUR_CM = 70

function Desk({ tintColor, standing, scaleX, scaleZ }) {
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

    const targetY = standing ? STAND_OFFSET_Y : 0
    const currentY = groupRef.current.position.y
    groupRef.current.position.y = currentY + (targetY - currentY) * t

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
      <color attach="background" args={['#e9e9ec']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 5, 2]} intensity={1.2} castShadow />
      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.8}>
          <Desk tintColor={tintColor} standing={hauteurMode === 'debout'} scaleX={scaleX} scaleZ={scaleZ} />
        </Bounds>
        <Environment preset="city" />
        <ContactShadows position={[0, -0.001, 0]} opacity={0.35} scale={10} blur={2.5} far={2} />
      </Suspense>
      <OrbitControls makeDefault />
    </Canvas>
  )
}

useGLTF.preload('/models/desk.glb')
