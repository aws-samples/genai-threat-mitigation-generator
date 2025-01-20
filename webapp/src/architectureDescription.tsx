import { ConnectorHook } from './amzn-genai-form/connector';
import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Form from '@cloudscape-design/components/form';
import { Box, CodeEditor } from '@cloudscape-design/components';
import Button from '@cloudscape-design/components/button';
import Markdown from 'markdown-to-jsx';

import ace from 'ace-builds';

ace.config.set('useStrictCSP', true);

import 'ace-builds/css/ace.css';

import 'ace-builds/src-noconflict/theme-dawn'
import 'ace-builds/css/theme/dawn.css';

import 'ace-builds/src-noconflict/theme-tomorrow_night_bright';
import 'ace-builds/css/theme/tomorrow_night_bright.css';

// Language support - Markdown
import 'ace-builds/src-noconflict/mode-markdown';
import 'ace-builds/src-noconflict/snippets/markdown';
import { DownloadButton } from './download.button.tsx';

export const useArchitectureDescription = (useConnector: ConnectorHook<any, any>) => {
  const [ description, setDescription ] = useState<string>('')
  const {
    submit,
    error,
    isLoading,
    completed,
    reset,
    data
  } = useConnector()

  return {
    description,
    setDescription,
    submit,
    error,
    isLoading,
    completed,
    reset,
    data
  }
}

interface ArchitectureDescriptionProps {
  value: string
  onChange: (value: string) => void
  isLoading: boolean
}

const i18nStrings = {
  loadingState: 'Loading code editor',
  errorState: 'There was an error loading the code editor.',
  errorStateRecovery: 'Retry',
  editorGroupAriaLabel: 'Code editor',
  statusBarGroupAriaLabel: 'Status bar',
  cursorPosition: (row, column) => `Ln ${ row }, Col ${ column }`,
  errorsTab: 'Errors',
  warningsTab: 'Warnings',
  preferencesButtonAriaLabel: 'Preferences',
  paneCloseButtonAriaLabel: 'Close',
  preferencesModalHeader: 'Preferences',
  preferencesModalCancel: 'Cancel',
  preferencesModalConfirm: 'Confirm',
  preferencesModalWrapLines: 'Wrap lines',
  preferencesModalTheme: 'Theme',
  preferencesModalLightThemes: 'Light themes',
  preferencesModalDarkThemes: 'Dark themes',
};


export const ArchitectureDescription = ({ value, onChange, isLoading }: ArchitectureDescriptionProps) => {
  const [ preferences, setPreferences ] = useState({});
  const [ isEditable, setIsEditable ] = useState(false)
  return <>
    <SpaceBetween direction="vertical" size="xl">
      <form>
        <Form
          header={ isEditable ? null : <Box>
            <SpaceBetween direction="horizontal" size="xs" alignItems={ 'end' }>
              <Button
                variant="primary"
                disabled={ isLoading }
                onClick={ () => setIsEditable(true) }
              >Edit</Button>
              <DownloadButton
                filename={'architecture'}
                value={value}
                disabled={isLoading}
              />
            </SpaceBetween>
          </Box> }
        >
          <SpaceBetween direction="vertical" size="m">
            { (isEditable && !isLoading) ?
              <CodeEditor ace={ ace }
                          value={ value }
                          loading={ isLoading }
                          language={ 'markdown' }
                          i18nStrings={ i18nStrings }
                          onPreferencesChange={ event => setPreferences(event.detail) }
                          onChange={ ({ detail }) => {
                            onChange(detail.value)
                          } }
                          themes={ { dark: [ 'dawn' ], light: [ 'tomorrow_night_bright' ] } }
                          preferences={ preferences }
              />
              :
              <>
                <Markdown options={ {} }>
                  { value || '' }
                </Markdown>
              </>
            }
          </SpaceBetween>
        </Form>
      </form>
    </SpaceBetween>
  </>
}
