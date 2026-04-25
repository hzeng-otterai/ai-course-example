import { render, screen } from '@testing-library/react'
import AutoSaveIndicator from './AutoSaveIndicator'

describe('AutoSaveIndicator', () => {
  it('renders "Saving..." for saving status', () => {
    render(<AutoSaveIndicator status="saving" />)
    expect(screen.getByText('Saving...')).toBeInTheDocument()
  })

  it('renders "Saved" for saved status', () => {
    render(<AutoSaveIndicator status="saved" />)
    expect(screen.getByText('Saved')).toBeInTheDocument()
  })

  it('renders "Save failed" for error status', () => {
    render(<AutoSaveIndicator status="error" />)
    expect(screen.getByText('Save failed')).toBeInTheDocument()
  })

  it('renders nothing for null status', () => {
    const { container } = render(<AutoSaveIndicator status={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing for undefined status', () => {
    const { container } = render(<AutoSaveIndicator />)
    expect(container).toBeEmptyDOMElement()
  })
})
