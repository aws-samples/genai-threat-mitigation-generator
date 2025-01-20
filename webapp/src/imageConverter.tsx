import { ConnectorHook } from './amzn-genai-form/connector';
import { useState } from 'react';
import { file } from './amzn-genai-form/form/input';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Form from '@cloudscape-design/components/form';

export const useImageConverter = (useConnector: ConnectorHook<any, any>) => {
  const [ value, setValue ] = useState<string>()
  const {
    submit,
    error,
    isLoading,
    completed,
    reset,
    data
  } = useConnector()
  return {
    value,
    onChange: setValue,
    error,
    isLoading,
    completed,
    reset,
    submit,
    data
  }
}

const FileUpload = file({
  label: 'Architecture diagram',
  required: true,
  uploadType: 'BASE64',
  accept: 'image/*',
  constraintText: 'Only images allowed',
  showFileThumbnail: true,
  showFileSize: true,
})['Component']

interface ConverterProps {
  onChange: (base64: string) => void,
  isLoading: boolean,
  error: Error | undefined,
}

export const ImageConverter = ({
                     onChange,
                     isLoading,
                     error,
                   }: ConverterProps) => {
  return <>
    <SpaceBetween direction="vertical" size="xl">
      <form>
        <Form>
          <SpaceBetween direction="vertical" size="m">
            <FileUpload
              onChange={ onChange }
              completed={ false }
              error={ error?.message || '' }
              isLoading={ isLoading }
            />
          </SpaceBetween>
        </Form>
      </form>
    </SpaceBetween>
  </>
}
