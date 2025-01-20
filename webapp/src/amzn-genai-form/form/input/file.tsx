import { useState } from 'react';
import FormField from '@cloudscape-design/components/form-field';
import { InputFieldType } from './types';
import { FileUpload } from '@cloudscape-design/components';

interface TextProps {
  label: string,
  accept: string,
  constraintText: string,
  required: boolean,
  showFileSize?: boolean
  showFileThumbnail?: boolean
  validation?: (value: string) => (string | undefined)
  uploadType?: 'BASE64'
}

export const file = ({
                       label,
                       required,
                       validation,
                       accept,
                       constraintText,
                       showFileSize,
                       showFileThumbnail,
                       uploadType
                     }: TextProps): InputFieldType => {

  const validator = (value: string): string | undefined => {
    if (required && !value) {
      return 'Field can not be empty'
    }
    if (validation) {
      return validation(value)
    }
    return undefined
  }
  const Component: InputFieldType['Component'] = ({ onChange, isLoading, completed, error }) => {
    const [ value, setValue ] = useState<ReadonlyArray<File>>([]);

    return <FormField
      label={ label }
      errorText={ error }
    >
        <FileUpload
          onChange={ ({ detail }) => {
            if (isLoading || completed) return;

            setValue(detail.value)
            switch (uploadType) {
              case 'BASE64': {
                const reader = new FileReader();
                reader.onload = () => {
                  console.log(reader.result, detail)
                  const bytes = Array.from(new Uint8Array(reader.result as ArrayBuffer));
                  const base64StringFile = btoa(bytes.map((item) => String.fromCharCode(item)).join(''));
                  onChange({
                    name: detail.value[0].name,
                    type: detail.value[0].type,
                    data: base64StringFile
                  })
                }
                reader.readAsArrayBuffer(detail.value[0]);
              }
            }
          } }
          value={ value }
          i18nStrings={ {
            uploadButtonText: e =>
              e ? 'Choose files' : 'Choose file',
            dropzoneText: e =>
              e
                ? 'Drop files to upload'
                : 'Drop file to upload',
            removeFileAriaLabel: e =>
              `Remove file ${ e + 1 }`,
            limitShowFewer: 'Show fewer files',
            limitShowMore: 'Show more files',
            errorIconAriaLabel: 'Error'
          } }
          showFileSize={ showFileSize }
          showFileThumbnail={ showFileThumbnail }
          multiple={ false }
          ariaRequired={ required }
          accept={ accept }
          constraintText={ constraintText }

        />
    </FormField>
  }

  return {
    validator,
    Component
  }
}