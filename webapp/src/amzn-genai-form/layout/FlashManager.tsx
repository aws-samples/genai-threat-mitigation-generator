import {
  createContext,
  PropsWithChildren,
  RefObject,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import Flashbar, { FlashbarProps } from '@cloudscape-design/components/flashbar';

interface FlashManagerContextValue {
  items: ReadonlyArray<FlashbarProps.MessageDefinition>
  ref: RefObject<ReadonlyArray<FlashbarProps.MessageDefinition>>
  setItems: (items: FlashbarProps.MessageDefinition[]) => void
}

export const FlashManagerContext = createContext<FlashManagerContextValue>(undefined as any)

export const FlashManagerProvider = FlashManagerContext.Provider
export const FlashManagerConsumer = FlashManagerContext.Consumer
export const useFlashManager = () => useContext(FlashManagerContext)

export const FlashManager = ({ children }: PropsWithChildren) => {
  const [ items, setItems ] = useState<FlashbarProps.MessageDefinition[]>([])
  const ref = useRef(items)

  const setter = useCallback((items: FlashbarProps.MessageDefinition[]) => {
    setItems(items)
    ref.current = items
  }, [ setItems ])

  return (
    <FlashManagerProvider value={ {
      items,
      setItems: setter,
      ref
    } }>
      { children }
    </FlashManagerProvider>
  )
}

export const FlashBar = () => {
  const { items } = useFlashManager()
  return (
    <Flashbar
      items={ items }
    />
  )
}

export const FlashMessage = (props: FlashbarProps.MessageDefinition) => {
  const { setItems, ref } = useFlashManager()
  const id = useMemo(() => {
    return props.id ?? String(Math.random() * 1000)
  }, [])
  const dismiss = useCallback(() => setItems(ref.current!.filter((item) => item.id !== id)), [])

  useEffect(() => {
    setItems([ ...ref.current!, {
      ...props,
      id: id,
      onDismiss: props.onDismiss ?? dismiss
    } ])
    return () => {
      dismiss()
    }
  }, [ props ])
  return null
}
