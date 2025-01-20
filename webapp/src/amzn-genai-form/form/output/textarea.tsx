import FormField from '@cloudscape-design/components/form-field';
import Textarea from '@cloudscape-design/components/textarea';
import { OutputFieldType } from './types';

interface TextareaProps {
  label: string
}

export const textarea = ({ label }: TextareaProps): OutputFieldType => {
  const Component: OutputFieldType['Component'] =  ({ value }) => {
    return <FormField
      label={ label }
    > <Textarea
      value={ value }
      readOnly
    />
    </FormField>
  }
  return {
    Component
  }
}
