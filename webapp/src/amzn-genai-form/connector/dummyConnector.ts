import { useCallback, useRef, useState } from 'react';
import { ConnectorData } from './types'

interface DummyConnectorInput {
  output: Promise<any>
  delay: number
}

export const dummyConnectorFactory = <I, O>({ output, delay }: DummyConnectorInput): (() => ConnectorData<I, O>) => {
  return () => {
    const [ data, setData ] = useState<O | undefined>(undefined)
    const [ isLoading, setIsLoading ] = useState(false)
    const [ completed, setCompleted ] = useState(false)
    const [ error, setError ] = useState<Error | undefined>(undefined)
    const queryRef = useRef<symbol>(Symbol(+new Date()))

    const reset = useCallback(() => {
      queryRef.current = Symbol(+new Date())
      setData(undefined)
      setIsLoading(false)
      setCompleted(false)
      setError(undefined)
    }, [])

    const submit = useCallback(async (input: I) => {
      const guard = Symbol(+new Date())
      queryRef.current = guard

      setData(undefined)
      setIsLoading(true)
      setCompleted(false)
      setError(undefined)

      try {
        console.log(input)
        await new Promise((resolve) => {
          setTimeout(resolve, delay)
        })
        if (queryRef.current !== guard) return

        const payload: O & { error: string } = await output
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