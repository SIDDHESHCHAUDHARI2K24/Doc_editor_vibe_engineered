import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useDocumentState } from './useDocumentState'
import * as editorApi from './api'

vi.mock('./api', () => ({
  getDocumentState: vi.fn(),
  putDocumentState: vi.fn(),
}))

const yjsListeners: Map<string, Set<() => void>> = new Map()

vi.mock('yjs', () => {
  return {
    Doc: class YDoc {
      on(event: string, fn: () => void) {
        if (!yjsListeners.has(event)) yjsListeners.set(event, new Set())
        yjsListeners.get(event)!.add(fn)
      }
      off(event: string, fn: () => void) {
        yjsListeners.get(event)?.delete(fn)
      }
      destroy() {
        yjsListeners.clear()
      }
      getText() {
        return { length: 0 }
      }
    },
    applyUpdate(_doc: unknown, _state: Uint8Array) { },
    encodeStateAsUpdate() {
      return new Uint8Array([1, 2, 3])
    },
  }
})

function triggerYjsUpdate() {
  const fns = yjsListeners.get('update')
  if (fns) {
    for (const fn of fns) {
      fn()
    }
  }
}

describe('useDocumentState save queue', () => {
  const mockGetState = vi.mocked(editorApi.getDocumentState)
  const mockPutState = vi.mocked(editorApi.putDocumentState)

  beforeEach(() => {
    vi.clearAllMocks()
    yjsListeners.clear()
    mockGetState.mockResolvedValue(new Uint8Array(0))
    mockPutState.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  async function renderAndWaitForDoc(docId = 'doc-1') {
    const rendered = renderHook(() => useDocumentState(docId))
    await waitFor(() => {
      expect(rendered.result.current.ydoc).not.toBeNull()
    })
    return rendered
  }

  it('saves changes after debounce period', async () => {
    const { result } = await renderAndWaitForDoc()

    vi.useFakeTimers()
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1499)
    expect(mockPutState).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    await vi.runAllTimersAsync()

    expect(mockPutState).toHaveBeenCalledTimes(1)
  })

  it('queues follow-up save when edits arrive during in-flight save', async () => {
    const resolvePromises: Array<() => void> = []
    mockPutState.mockImplementation(() =>
      new Promise<void>((resolve) => { resolvePromises.push(resolve) })
    )

    const { result } = await renderAndWaitForDoc()

    vi.useFakeTimers()

    // 1. Type: debounce → save starts
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(1)

    // 2. While save 1 is in-flight, type more: debounce → performSave
    //    should set pendingSaveRef since savingRef is true
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()
    // performSave was called but returned early (savingRef=true)
    // pendingSaveRef should now be true

    // 3. Resolve save 1 → finally should see pendingSaveRef and queue save 2
    act(() => { resolvePromises.shift()!() })
    await vi.runAllTimersAsync()

    // 4. The 0ms follow-up debounce fires → save 2 starts
    vi.advanceTimersByTime(0)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(2)
  })

  it('does not drop multiple rounds of edits during saves', async () => {
    const resolvePromises: Array<() => void> = []
    mockPutState.mockImplementation(() =>
      new Promise<void>((resolve) => { resolvePromises.push(resolve) })
    )

    const { result } = await renderAndWaitForDoc()

    vi.useFakeTimers()

    // Round 1
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(1)

    // Edit while save 1 is in-flight
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()

    // Resolve save 1 → queue save 2
    act(() => { resolvePromises.shift()!() })
    await vi.runAllTimersAsync()
    vi.advanceTimersByTime(0)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(2)

    // Edit while save 2 is in-flight
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()

    // Resolve save 2 → queue save 3
    act(() => { resolvePromises.shift()!() })
    await vi.runAllTimersAsync()
    vi.advanceTimersByTime(0)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(3)
  })

  it('force-save triggers even during in-flight save', async () => {
    const resolvePromises: Array<() => void> = []
    mockPutState.mockImplementation(() =>
      new Promise<void>((resolve) => { resolvePromises.push(resolve) })
    )

    const { result } = await renderAndWaitForDoc()

    vi.useFakeTimers()

    // Trigger first save
    act(() => { triggerYjsUpdate() })
    vi.advanceTimersByTime(1500)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(1)

    // forceSave while save 1 is in-flight — should mark pending
    act(() => { result.current.forceSave() })
    await vi.runAllTimersAsync()

    // Resolve save 1 → pending should trigger save 2
    act(() => { resolvePromises.shift()!() })
    await vi.runAllTimersAsync()
    vi.advanceTimersByTime(0)
    await vi.runAllTimersAsync()
    expect(mockPutState).toHaveBeenCalledTimes(2)
  })
})
