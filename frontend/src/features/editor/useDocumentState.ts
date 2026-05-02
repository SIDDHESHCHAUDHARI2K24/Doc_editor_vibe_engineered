import { useState, useEffect, useRef, useCallback } from 'react'
import * as Y from 'yjs'
import { getDocumentState, putDocumentState } from './api'
import type { ApiError } from '@/lib/api/apiClient'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export interface UseDocumentStateResult {
  ydoc: Y.Doc | null
  status: SaveStatus
  lastError: string | null
  lastErrorStatus: number | null
  hasPendingChanges: boolean
  forceSave: () => void
}

export function useDocumentState(docId: string): UseDocumentStateResult {
  const [ydoc, setYdoc] = useState<Y.Doc | null>(null)
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [lastError, setLastError] = useState<string | null>(null)
  const [lastErrorStatus, setLastErrorStatus] = useState<number | null>(null)
  const [hasPendingChanges, setHasPendingChanges] = useState(false)
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const savingRef = useRef(false)
  const pendingSaveRef = useRef(false)
  const docRef = useRef<Y.Doc | null>(null)
  const docIdRef = useRef(docId)

  docIdRef.current = docId

  // Mount: fetch state, hydrate Yjs doc
  useEffect(() => {
    let cancelled = false
    const doc = new Y.Doc()
    docRef.current = doc

    void (async () => {
      try {
        const state = await getDocumentState(docId)
        if (!cancelled && state.byteLength > 0) {
          Y.applyUpdate(doc, state)
        }
        if (!cancelled) {
          setYdoc(doc)
          setStatus('saved')
          setLastError(null)
          setLastErrorStatus(null)
          setHasPendingChanges(false)
        }
      } catch (e) {
        if (!cancelled) {
          const apiErr = e as ApiError
          setLastError(apiErr.message)
          setLastErrorStatus(apiErr.status ?? null)
          setStatus('error')
        }
      }
    })()

    return () => {
      cancelled = true
      doc.destroy()
      docRef.current = null
    }
  }, [docId])

  const performSave = useCallback(async (doc: Y.Doc, id: string) => {
    if (savingRef.current) {
      pendingSaveRef.current = true
      return
    }
    savingRef.current = true
    pendingSaveRef.current = false
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
      debounceTimer.current = null
    }
    setStatus('saving')
    setHasPendingChanges(true)
    try {
      const state = Y.encodeStateAsUpdate(doc)
      await putDocumentState(id, state)
      setStatus('saved')
      setHasPendingChanges(false)
      setLastError(null)
      setLastErrorStatus(null)
    } catch (e) {
      const apiErr = e as ApiError
      setStatus('error')
      setLastError(apiErr.message)
      setLastErrorStatus(apiErr.status ?? null)
    } finally {
      savingRef.current = false
      if (pendingSaveRef.current) {
        if (debounceTimer.current) {
          clearTimeout(debounceTimer.current)
        }
        debounceTimer.current = setTimeout(() => {
          debounceTimer.current = null
          if (docRef.current) {
            void performSave(docRef.current, docIdRef.current)
          }
        }, 0)
      }
    }
  }, [])

  // Save on debounced Yjs change
  useEffect(() => {
    if (!ydoc) return

    const onUpdate = () => {
      setHasPendingChanges(true)
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
      debounceTimer.current = setTimeout(() => {
        debounceTimer.current = null
        if (docRef.current) {
          void performSave(docRef.current, docIdRef.current)
        }
      }, 1500)
    }

    ydoc.on('update', onUpdate)

    return () => {
      ydoc.off('update', onUpdate)
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
        debounceTimer.current = null
      }
    }
  }, [ydoc, performSave])

  const forceSave = useCallback(() => {
    const doc = docRef.current
    if (!doc) return
    void performSave(doc, docIdRef.current)
  }, [performSave])

  return { ydoc, status, lastError, lastErrorStatus, hasPendingChanges, forceSave }
}
