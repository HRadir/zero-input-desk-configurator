import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Bounds, ContactShadows, Environment, OrbitControls, useGLTF } from '@react-three/drei'
import { useCatalogueStore } from '../store/useCatalogueStore'
import { useConfigStore } from '../store/useConfigStore'

// Translation verticale approximative "debout" vs "assis", en unités du modèle.
// Le GLB source n'a ni rig ni animation (cf. MODEL_NOTES.md) : on simule le mouvement
// en déplaçant tout le bureau en bloc plutôt que de télescoper les pieds individuellement.
const STAND_OFFSET_Y = 0.12

function Desk({ tintColor, standing }) {
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
    const target = standing ? STAND_OFFSET_Y : 0
    const current = groupRef.current.position.y
    const t = Math.min(delta * 4, 1)
    groupRef.current.position.y = current + (target - current) * t
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
  const tintColor = finition?.couleur_hex ?? '#ffffff'

  return (
    <Canvas shadows camera={{ fov: 45, position: [3, 2.2, 4] }}>
      <color attach="background" args={['#e9e9ec']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 5, 2]} intensity={1.2} castShadow />
      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.4}>
          <Desk tintColor={tintColor} standing={hauteurMode === 'debout'} />
        </Bounds>
        <Environment preset="city" />
        <ContactShadows position={[0, -0.001, 0]} opacity={0.35} scale={10} blur={2.5} far={2} />
      </Suspense>
      <OrbitControls makeDefault />
    </Canvas>
  )
}

useGLTF.preload('/models/desk.glb')
