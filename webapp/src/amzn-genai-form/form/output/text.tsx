import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import { OutputFieldType } from './types';

interface TextProps {
  label: string
}

export const text = ({ label }: TextProps): OutputFieldType => {
  const Component: OutputFieldType['Component'] = ({ value }) => {
    return <FormField
      label={ label }
    > <Input
      value={ value }
      readOnly
    />
    </FormField>
  }
  return {
    Component
  }
}
