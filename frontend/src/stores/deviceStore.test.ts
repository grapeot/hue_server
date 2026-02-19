import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDeviceStore } from './deviceStore'

describe('deviceStore', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn()
    useDeviceStore.setState({ status: null, error: null })
  })

  it('has initial state', () => {
    const state = useDeviceStore.getState()
    expect(state.status).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('fetchStatus merges partial data with existing status', async () => {
    const mockFetch = vi.mocked(globalThis.fetch)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ wemo: { coffee: { is_on: true } } }),
    } as Response)

    useDeviceStore.setState({
      status: {
        hue: { name: 'Baby room', is_on: true, brightness: 128 } as any,
        wemo: {},
        rinnai: {} as any,
        garage: {} as any,
      },
    })

    await useDeviceStore.getState().fetchStatus(['wemo'])

    const status = useDeviceStore.getState().status
    expect(status?.hue?.name).toBe('Baby room')
    expect(status?.wemo?.coffee?.is_on).toBe(true)
  })
})
