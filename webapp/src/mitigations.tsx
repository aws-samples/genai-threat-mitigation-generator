import SpaceBetween from '@cloudscape-design/components/space-between';
import Form from '@cloudscape-design/components/form';
import Box from '@cloudscape-design/components/box';
import Markdown from 'markdown-to-jsx';
import { DownloadButton } from './download.button.tsx';

interface MitigationsViewProps {
  value: string
  isLoading: boolean
}

export const MitigationsView = ({ value, isLoading }: MitigationsViewProps) => {
  return <SpaceBetween direction="vertical" size="xl">
    <form>
      <Form
        header={ <Box>
          <SpaceBetween direction="horizontal" size="xs" alignItems={ 'end' }>
            <DownloadButton filename={'mitigations'} value={value} disabled={isLoading} />
          </SpaceBetween>
        </Box> }
      >
        <SpaceBetween direction="vertical" size="m">
          <>
            <Markdown options={ {} }>
              { value || '' }
            </Markdown>
          </>
        </SpaceBetween>
      </Form>
    </form>
  </SpaceBetween>
}