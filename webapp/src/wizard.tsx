import { Wizard } from '@cloudscape-design/components';
import { ImageConverter, useImageConverter } from './imageConverter.tsx';
import { ArchitectureDescription, useArchitectureDescription } from './architectureDescription.tsx';
import { MitigationsView } from './mitigations.tsx';
import { ConnectorHook } from './amzn-genai-form/connector';
import { useEffect, useState } from 'react';
import Markdown from 'markdown-to-jsx'
import { FormLoadingBar } from './amzn-genai-form/layout/FormLoadingBar.tsx';
import Box from '@cloudscape-design/components/box';
import { DownloadButton } from './download.button.tsx';

interface WizardOptions {
  imageConverterConnector: ConnectorHook<any, any>
  architectureDescriptionConnector: ConnectorHook<any, any>
}

const useWizard = ({
                     imageConverterConnector,
                     architectureDescriptionConnector
                   }: WizardOptions) => {
  const [ activeStepIndex, setActiveStepIndex ] = useState(0);
  const [ navigationError, setNavigationError ] = useState<string>('')
  const [ wizardKey, setWizardKey ] = useState(() => Math.random())
  const [ completed, setCompleted ] = useState(false)
  const imageConverterState = useImageConverter(imageConverterConnector)

  const architectureDescriptionState = useArchitectureDescription(architectureDescriptionConnector)

  useEffect(() => {
    window.scroll({
      top: 0,
      behavior: 'auto'
    })
  }, [ imageConverterState.isLoading, architectureDescriptionState.isLoading ]);

  useEffect(() => {
    architectureDescriptionState.setDescription(imageConverterState.data?.content)
  }, [ imageConverterState.data?.content, imageConverterState.isLoading, imageConverterState.completed ]);

  const handleImageChange = async (base64: string) => {
    setNavigationError('')
    imageConverterState.onChange(base64)
    imageConverterState.submit({ content: base64 })
    setActiveStepIndex(1)
  }

  const handleCancel = () => {
    imageConverterState.reset()
    architectureDescriptionState.reset()
    architectureDescriptionState.setDescription('')
    setActiveStepIndex(0)
    setWizardKey(Math.random())
  }

  const handleNavigation = async ({ detail }: Omit<CustomEvent<{
    reason: string,
    requestedStepIndex: number
  }>, 'preventDefault'>) => {
    if (activeStepIndex === 0 && detail.reason === 'next' && !imageConverterState.data) {
      setNavigationError('Diagram not uploaded yet')
      return
    }
    if (activeStepIndex === 1 && detail.reason === 'next') {
      architectureDescriptionState.submit({ content: architectureDescriptionState.description })
    }
    setNavigationError('')
    setActiveStepIndex(detail.requestedStepIndex)
    window.scroll({
      top: 0,
      behavior: 'auto'
    })
  }

  const handleSubmit = () => {
    setCompleted(true)
    window.scroll({
      top: 0,
      behavior: 'auto'
    })
  }

  const isLoading = imageConverterState.isLoading || architectureDescriptionState.isLoading
  const error = imageConverterState.error?.message || navigationError
  return {
    handleImageChange,
    isLoading,
    error,
    imageConverter: {
      output: imageConverterState.data?.content,
      handleChange: handleImageChange,
      isLoading: imageConverterState.isLoading,
      error: imageConverterState.error
    },
    architectureDescription: {
      output: architectureDescriptionState.data?.content,
      value: architectureDescriptionState.description,
      handleChange: architectureDescriptionState.setDescription,
      isLoading: architectureDescriptionState.isLoading,
      error: architectureDescriptionState.error
    },
    completed,
    handleNavigation,
    handleSubmit,
    handleCancel,
    wizardKey,
    activeStepIndex,
    setActiveStepIndex,
    navigationError,
    setNavigationError
  }
}

interface Props {
  imageConverterConnector: ConnectorHook<any, any>
  architectureDescriptionConnector: ConnectorHook<any, any>
}

export const MitigationsWizard = ({ imageConverterConnector, architectureDescriptionConnector }: Props) => {
  const {
    activeStepIndex,
    architectureDescription,
    imageConverter,
    wizardKey,
    handleCancel,
    handleNavigation,
    handleSubmit,
    completed,
    isLoading,
    navigationError,
  } = useWizard({
    imageConverterConnector,
    architectureDescriptionConnector
  })

  if (completed) {
    return <>
      <Box>
        <DownloadButton filename={ 'mitigations' } value={ architectureDescription.output }/>
      </Box>
      <Markdown options={ {} }>
        { architectureDescription.output }
      </Markdown>
    </>
  }

  return <>
    { isLoading && <FormLoadingBar/> }
    <Wizard
      isLoadingNextStep={ isLoading }
      allowSkipTo={ false }
      onCancel={ handleCancel }
      steps={ [
        {
          title: 'Upload architecture diagram',
          description: 'Convert using LLM',
          content: <>
            {/*{isLoading && <FormLoadingBar/>}*/ }
            <ImageConverter
              onChange={ imageConverter.handleChange }
              error={ imageConverter.error }
              isLoading={ imageConverter.isLoading }
              key={ wizardKey }
            />
          </>,
          errorText: imageConverter.error?.message || navigationError
        },
        {
          title: 'Review architecture',
          description: 'Review and adjust if necessary',
          errorText: architectureDescription.error?.message || navigationError,
          content: <>
            {/*{isLoading && <FormLoadingBar/>}*/ }
            <ArchitectureDescription
              value={ architectureDescription.value }
              onChange={ architectureDescription.handleChange }
              isLoading={ imageConverter.isLoading || architectureDescription.isLoading }
            />
          </>,
        },
        {
          title: 'Review mitigations',
          description: `Let's see what LLM prepared for us`,
          errorText: navigationError,
          content: <>
            {/*{isLoading && <FormLoadingBar/>}*/ }
            <MitigationsView
              value={ architectureDescription.output || '' }
              isLoading={ architectureDescription.isLoading }
            />
          </>
        }
      ] }
      i18nStrings={ {
        stepNumberLabel: stepNumber =>
          `Step ${ stepNumber }`,
        collapsedStepsLabel: (stepNumber, stepsCount) =>
          `Step ${ stepNumber } of ${ stepsCount }`,
        skipToButtonLabel: (step, _stepNumber) =>
          `Skip to ${ step.title }`,
        navigationAriaLabel: 'Steps',
        cancelButton: 'Restart',
        previousButton: 'Previous',
        nextButton: 'Next',
        submitButton: 'Finish',
        optional: 'optional'
      } }
      onNavigate={ handleNavigation }
      activeStepIndex={ activeStepIndex }
      onSubmit={ handleSubmit }
    />
  </>
}
