import { FormEvent, useEffect, useState } from 'react';
import {  ConnectorHook } from '../connector'
import SpaceBetween from '@cloudscape-design/components/space-between';
import Form from '@cloudscape-design/components/form';
import Button from '@cloudscape-design/components/button';
import Container from '@cloudscape-design/components/container';

import * as FormInput from './input'
import * as FormOutput from './output'
import Header from '@cloudscape-design/components/header';
import { FlashMessage } from '../layout/FlashManager';


interface Props {
  inputFields: Record<string, FormInput.InputFieldType>
  outputFields: Record<string, FormOutput.OutputFieldType>
  useConnector: ConnectorHook<any, any>
  onError?: (error: Error) => void
  onCompleted?: (data: Record<string, any>) => void
  onChange?: (data: Record<string, any> | undefined) => void
  onReset?: () => void
}

export const GenAiForm = ({ inputFields, outputFields, useConnector, onReset, onCompleted, onError, onChange }: Props) => {
  const {
    error,
    isLoading,
    data,
    submit,
    completed,
    reset
  } = useConnector()
  const [ state, setState ] = useState<Record<keyof typeof inputFields, any>>({})
  const [ formError, setFormError ] = useState<Record<keyof typeof inputFields, string>>({})

  useEffect(() => {
    onChange?.(state)
  }, [state])

  const handleReset = () => {
    reset()
    onReset?.()
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errors: Record<keyof typeof inputFields, string> = {}
    Object.entries(inputFields).forEach(([key, {validator}]) => {
      const errorMessage = validator(state[key])
      if (errorMessage) {
        errors[key] = errorMessage
      }
    })
    setFormError(errors)
    if (Object.keys(errors).length === 0) {
      submit(state)
        .then((payload) => {
          if (payload)
            onCompleted?.(payload)
        })
        .catch((error) => {
          onError?.(error)
        })
    }
  }

  return (
    <>
      { error && <FlashMessage type="error" content={ `Error occurred: ${ error?.message }` } dismissible/> }
      <SpaceBetween direction="vertical" size="xl">
        <form onSubmit={ handleSubmit }>
          <Form
            actions={ completed ? null :
              <Button variant="primary" disabled={ isLoading } loading={ isLoading }>Run</Button>
            }
          >
            <Container
              header={
                <Header variant="h2"
                        actions={ completed
                          ? <Button variant="primary" onClick={ (event) => {
                            event.preventDefault()
                            handleReset()
                          } }>New query</Button>
                          : null }
                >
                  Query
                </Header>
              }
            >
              <SpaceBetween direction="vertical" size="m">
                { Object.entries(inputFields).map(([ key, { validator, Component } ]) => (
                  <Component
                    key={ key }
                    isLoading={ isLoading }
                    completed={completed}
                    error={ formError[key] }
                    onChange={ (value: any) => {
                      const errors = { ...formError }
                      const errorMessage = validator(value)
                      if (errorMessage) {
                        errors[key] = errorMessage
                      } else {
                        delete errors[key]
                      }
                      setFormError(errors)
                      setState({ ...state, [key]: value })
                    }}
                  />
                )) }
              </SpaceBetween>
            </Container>
          </Form>
        </form>
        { data && <Container
          header={ <Header variant="h2">Result</Header> }
        >
            <SpaceBetween direction="vertical" size="l">
              { Object.entries(outputFields).map(([ key, { Component } ]) => (
                <Component
                  key={ key }
                  value={ data ? data[key] : undefined }
                />
              )) }
            </SpaceBetween>
        </Container>
        }
      </SpaceBetween>
    </>
  )
}
