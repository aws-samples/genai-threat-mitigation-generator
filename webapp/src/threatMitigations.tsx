import { Tabs } from '@cloudscape-design/components';
import { formInput, formOutput, GenAiForm, connectors } from './amzn-genai-form';
import { useEffect, useState } from 'react';
import { useStorage } from './amzn-genai-form/useStorage.ts';
import { useNavigate, useParams } from 'react-router-dom';

const pathThreats = ''

const connector = connectors.dummyConnectorFactory({
  output: Promise.resolve({
    id: '1',
    content: 'This is a sample response'
  }),
  delay: 2500
})

export const ThreatMitigations = () => {

  const {id: activeTabId} = useParams<{id: string}>()
  const navigate = useNavigate()

  const { list, set} = useStorage();
  const [data, setData] = useState<Record<string, string>>({})

  useEffect(() => {
    list()
      .then((items) => {
        const reduced = items.reduce<Record<string, string>>((acc, item) => {
          acc[item.key] = item.value
          return acc
        }, {})

        setData(reduced)
      })
  }, [])

  function renderThreatMitigations(key: string, value: string) {
    return <GenAiForm
      useConnector={ connector }
      key={key}
      onChange={(update) => {
        if (!update || update.text === undefined) return
        set(key, {
          key: key,
          value: update.text
        })
      }}
      inputFields={{
        text: formInput.textarea({
          label: 'Text',
          required: true,
          initialValue:  value,
          placeholder: 'Diagram description'
          // rows: 15,
        })
      } }
      outputFields={ {
        content: formOutput.textarea({
          label: 'Text',
        })
      }}
    />
  }

  return <Tabs
    activeTabId={activeTabId}
    onChange={({ detail }) => {
      set(detail.activeTabId, {
        key: detail.activeTabId,
        value: data[detail.activeTabId] || ''
      })
      navigate(`/${pathThreats}/${detail.activeTabId}`)
    }}
    tabs={Object.entries(data).map(([key, value]) => ({
      label: key,
      id: key,
      content: renderThreatMitigations(key, value)
    }))}
  />
}