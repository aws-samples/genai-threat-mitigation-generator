import BreadcrumbGroup from '@cloudscape-design/components/breadcrumb-group';
import { FlashBar, FlashManager } from './FlashManager';
import { PropsWithChildren, useState } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Header from '@cloudscape-design/components/header';

interface Props extends PropsWithChildren {
  pageTitle: string
  description: string
  breadcrumbs?: Array<{ text: string, href: string }>
  navigation?: React.ReactNode
  tools?: React.ReactNode
}

export const GenAiLayout = ({ children, pageTitle, breadcrumbs, navigation, tools }: Props) => {

  const [isNavigationVisible, setIsNavigationVisible] = useState(!!navigation)
  const [isToolsVisible, setIsToolsVisible] = useState(!!tools)

  function renderBreadcrumbs() {
    if (!breadcrumbs?.length) return null
    return <BreadcrumbGroup
      items={ breadcrumbs }
    />
  }

  function renderNotifications() {
    return <>
      <FlashBar/>
    </>
  }

  function renderContent() {
    return <ContentLayout
      header={
        <Header
          variant="h1"
        >
          { pageTitle }
        </Header>
      }
    >
      {children}
    </ContentLayout>
  }

  return (
    <FlashManager>
      <AppLayout
        breadcrumbs={ renderBreadcrumbs() }
        navigation={navigation}
        navigationOpen={isNavigationVisible}
        onNavigationChange={() => setIsNavigationVisible(!isNavigationVisible)}
        notifications={ renderNotifications() }
        tools={tools}
        toolsOpen={isToolsVisible}
        onToolsChange={() => setIsToolsVisible(!isToolsVisible)}
        contentType={ 'form' }
        content={ renderContent() }
      />
    </FlashManager>
  );
}