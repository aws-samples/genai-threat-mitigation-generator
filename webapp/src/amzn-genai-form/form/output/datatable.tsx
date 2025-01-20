import FormField from '@cloudscape-design/components/form-field';
import { OutputFieldType } from './types';
import { Box, Table } from '@cloudscape-design/components';
import SpaceBetween from '@cloudscape-design/components/space-between';

interface TextareaProps {
  label: string
}

export const datatable = ({ label }: TextareaProps): OutputFieldType => {
  const Component: OutputFieldType['Component'] = ({ value }) => {
    return <FormField
      label={ label }
    >
      <Table
        items={ value || [] }
        loadingText="Loading data"
        sortingDisabled
        empty={
          <Box
            margin={ { vertical: 'xs' } }
            textAlign="center"
            color="inherit"
          >
            <SpaceBetween size="m">
              <b>No data for current query</b>
            </SpaceBetween>
          </Box>
        }
        columnDefinitions={ value?.length > 0 ? Object.keys(value[0]).map(key => ({
          id: key,
          header: key,
          cell(item: any): React.ReactNode {
            return item[key]
          }
        })) : []
        }
      />
    </FormField>
  }
  return {
    Component
  }
}
