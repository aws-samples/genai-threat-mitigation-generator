import { useCallback, useRef, useState } from 'react';
import { ConnectorData } from './types'

interface FetchConnectorInput {
  url: string
  headers?: Record<string, string>,
  fetch?: typeof fetch
}

export const fetchConnectorFactory = <I, O>({ url, headers, fetch = global.fetch }: FetchConnectorInput): (() => ConnectorData<I, O>) => {
  return () => {
    const [ data, setData ] = useState<O | undefined>(undefined)
    const [ isLoading, setIsLoading ] = useState(false)
    const [ completed, setCompleted ] = useState(false)
    const [ error, setError ] = useState<Error | undefined>(undefined)
    const queryRef = useRef<symbol>(Symbol(+new Date()))
    const abortControllerRef = useRef(new AbortController())

    const reset = useCallback(() => {
      queryRef.current = Symbol(+new Date())

      abortControllerRef.current.abort()
      abortControllerRef.current = new AbortController()

      setData(undefined)
      setIsLoading(false)
      setCompleted(false)
      setError(undefined)
    }, [])

    const submit = useCallback(async (input: I) => {
      const guard = Symbol(+new Date())
      queryRef.current = guard

      abortControllerRef.current.abort()
      abortControllerRef.current = new AbortController()

      setData(undefined)
      setIsLoading(true)
      setCompleted(false)
      setError(undefined)

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            ...(headers || {})
          },
          body: JSON.stringify(input),
          signal: abortControllerRef.current.signal
        })
        if (queryRef.current !== guard) return

        let payload: O & { error?: string | undefined } = {} as any
        if (response.headers.get('content-type')?.startsWith('text/event-stream')) {
          for await (const chunk of response.body as unknown as AsyncIterable<any>) {
            const chunkString = new TextDecoder('utf-8').decode(chunk);
            const regex = /^data: (.*)$/gm;
            const matchedChunks = chunkString.match(regex) as RegExpMatchArray;
            if (!matchedChunks) continue
            for (const matchedChunk of matchedChunks) {
              // slice for removing "data: " after regExp match
              const json = JSON.parse(matchedChunk.slice(5));
              payload = Object.keys(json).reduce<O & { error?: string | undefined }>((container, key) => {
                container[key] = container[key] ? `${ container[key] }${ json[key] }` : json[key]
                return container
              }, { ...payload
              })
              setData(payload)
            }
          }
        } else {
          payload = await response.json()
        }

        setIsLoading(false)
        setData(payload)
        setError(payload?.error ? new Error(payload.error) : undefined)
        setCompleted(true)

        return payload
      } catch (e: any) {
        if (queryRef.current !== guard) return
        setError(e)
        setIsLoading(false)
        throw e
      }
    }, [])

    return {
      isLoading,
      completed,
      error,
      reset,
      submit,
      data
    }
  }
}