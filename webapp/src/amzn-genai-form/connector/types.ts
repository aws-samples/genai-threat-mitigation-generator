export interface ConnectorData<I, O> {
  isLoading: boolean,
  completed: boolean
  error: Error | undefined,
  reset: () => void,
  submit: (input: I) => Promise<undefined | O>
  data: O | undefined
}

export type ConnectorHook<I, O> = () => ConnectorData<I, O>
