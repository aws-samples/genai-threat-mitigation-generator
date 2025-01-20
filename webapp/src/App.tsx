import '@cloudscape-design/global-styles/index.css';
import { connectors, GenAiLayout } from './amzn-genai-form'
import { HelpPanel, SideNavigation } from '@cloudscape-design/components';
import { MitigationsWizard } from './wizard.tsx';
import {AwsConfig, basePath, createFetcher} from './config'

const fetch = await createFetcher()
const imageConverterConnector = connectors.fetchConnectorFactory({
  url: AwsConfig.endpoints.diagramToText,
    fetch: fetch
})
const mitigationsConnector = connectors.fetchConnectorFactory({
  url: AwsConfig.endpoints.summaryToThreatModel,
    fetch: fetch
})

const App = () => {
  return (
    <>
      <GenAiLayout
        pageTitle={ 'Threat mitigation tool' }
        breadcrumbs={ [] }
        tools={
          <HelpPanel header={ <h2>Overview</h2> }>Threat mitigation tool</HelpPanel>
        }
        navigation={
          <SideNavigation
            header={ {
              href: `/threat-mitigation`,
              text: 'Threat Mitigation Tool',
            } }
            activeHref={ document.location.pathname }
            items={ [
              { type: 'link', text: `Threat Mitigation`, href: `${ basePath }`, }
            ] }
          />
        }
        description={ 'Tool description' }
      >
        <MitigationsWizard
          imageConverterConnector={imageConverterConnector}
          architectureDescriptionConnector={mitigationsConnector}
        />
      </GenAiLayout>
    </>
  );
}

export default App
