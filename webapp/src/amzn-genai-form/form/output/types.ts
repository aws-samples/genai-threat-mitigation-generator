import { ComponentType } from 'react';

export interface OutputComponentProps {
  value: any
}

export type OutputFieldType = {
  Component: ComponentType<OutputComponentProps>
}
