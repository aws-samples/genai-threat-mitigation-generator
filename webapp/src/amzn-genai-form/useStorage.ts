import { useCallback } from 'react';

const prefix = `threat-mitigation+`

export interface StorageItem {
  key: string
  value: string
}

export const useStorage = () => {

  const list = useCallback(async (): Promise<StorageItem[]> => {
    return Object.keys(localStorage)
      .filter(item => item.startsWith(prefix))
      .map(item => localStorage.getItem(item))
      .filter((item): item is string => !!item && typeof item === 'string')
      .map(item => JSON.parse(item))
  }, [])

  const get = useCallback(async (key: string): Promise<StorageItem | undefined> => {
    const item = localStorage.getItem(prefix + key)
    if (item) {
      return JSON.parse(item)
    }
  }, [])

  const set = useCallback(async (key: string, value: StorageItem) => {
    return localStorage.setItem(prefix + key, JSON.stringify(value))
  }, [])

  const remove = useCallback(async (key: string) => {
    return localStorage.removeItem(prefix + key)
  }, [])

  return { list, get, set, remove }
}