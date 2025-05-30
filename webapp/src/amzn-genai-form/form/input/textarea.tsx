import { useEffect, useState } from 'react';
import FormField from '@cloudscape-design/components/form-field';
import { InputFieldType } from './types';
import { Textarea } from '@cloudscape-design/components';

interface TextareaProps {
  initialValue?: string,
  label: string,
  placeholder: string,
  required: boolean,
  validation?: (value: string) => (string | undefined)
}

export const textarea = ({ label, placeholder, required, validation, initialValue }: TextareaProps): InputFieldType => {
  const validator = (value: string): string | undefined => {
    if (required && (!value || !String(value).trim())) {
      return 'Field can not be empty'
    }
    if (validation) {
      return validation(value)
    }
    return undefined
  }
  const Component: InputFieldType['Component'] = ({ onChange, isLoading, completed, error }) => {
    const [ value, setValue ] = useState(initialValue || '')
    useEffect(() => {
      onChange(initialValue || '')
    }, [])
    return <FormField
      label={ label }
      errorText={error}
    > <Textarea
      value={ value }
      onChange={ ({ detail }) => {
        setValue(detail.value)
        onChange(detail.value)
      }}
      onBlur={() => {
        onChange(value)
      }}
      placeholder={ placeholder }
      disabled={ isLoading || completed }
    />
    </FormField>
  }

  return {
    validator,
    Component
  }
}