import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Erreur dans le viewer 3D :', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="viewer-error">
          <p>Impossible de charger le modèle 3D du bureau.</p>
          <p className="viewer-error-detail">{this.state.error.message}</p>
        </div>
      )
    }
    return this.props.children
  }
}
