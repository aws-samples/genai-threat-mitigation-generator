import { ComponentType } from 'react';

export interface InputComponentProps {
  onChange: (value: any) => void
  error: string
  isLoading: boolean
  completed: boolean
}

export type InputFieldType = {
  validator: (value: any) => string | undefined,
  Component: ComponentType<InputComponentProps>
}
