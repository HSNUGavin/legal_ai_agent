import { useState, useEffect, useRef } from 'react'
import {
  Box,
  VStack,
  Input,
  Button,
  Text,
  Container,
  Flex,
  useToast,
  ButtonGroup,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  HStack,
} from '@chakra-ui/react'
import { ChevronDownIcon, AddIcon } from '@chakra-ui/icons'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Conversation {
  id: string
  last_update: string
  messages_count: number
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const toast = useToast()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await fetch('/api/conversations')
        const data = await response.json()
        setConversations(data)
        if (data.length > 0 && !currentConversationId) {
          setCurrentConversationId(data[0].id)
        }
      } catch (error) {
        console.error('Error fetching conversations:', error)
      }
    }
    fetchConversations()
  }, [currentConversationId])

  useEffect(() => {
    if (!currentConversationId) return

    const websocket = new WebSocket(`ws://${window.location.host}/ws/${currentConversationId}`)
    
    websocket.onopen = () => {
      toast({
        title: '已連接到伺服器',
        status: 'success',
        duration: 2000,
        isClosable: true,
      })
    }

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'status') {
        if (message.content === 'done') {
          setIsProcessing(false)
        }
      } else if (message.type === 'history') {
        setMessages(message.content)
      } else {
        setMessages(prev => [...prev, message])
        if (message.role === 'assistant') {
          setIsProcessing(false)
        }
      }
    }

    websocket.onerror = () => {
      toast({
        title: '連接錯誤',
        status: 'error',
        duration: 2000,
        isClosable: true,
      })
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [toast, currentConversationId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!input.trim() || !ws) return

    const message = {
      role: 'user' as const,
      content: input,
    }

    setIsProcessing(true)
    ws.send(JSON.stringify(message))
    setInput('')
  }

  const handleStop = () => {
    if (!ws) return
    ws.send(JSON.stringify({ type: 'stop' }))
    setIsProcessing(false)
    toast({
      title: '已停止處理',
      status: 'info',
      duration: 2000,
      isClosable: true,
    })
  }

  const createNewConversation = async () => {
    try {
      const response = await fetch('/api/conversations', {
        method: 'POST',
      })
      const data = await response.json()
      setConversations(prev => [...prev, data])
      setCurrentConversationId(data.id)
      setMessages([])
    } catch (error) {
      console.error('Error creating new conversation:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  return (
    <Container maxW="container.md" py={8}>
      <VStack spacing={4} align="stretch" h="100vh">
        <HStack spacing={2}>
          <Menu>
            <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
              {currentConversationId ? 
                `對話 ${conversations.find(c => c.id === currentConversationId)?.last_update}` : 
                '選擇對話'}
            </MenuButton>
            <MenuList>
              {conversations.map((conv) => (
                <MenuItem 
                  key={conv.id} 
                  onClick={() => setCurrentConversationId(conv.id)}
                >
                  更新於 {formatDate(conv.last_update)} ({conv.messages_count} 則訊息)
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
          <IconButton
            aria-label="新對話"
            icon={<AddIcon />}
            onClick={createNewConversation}
          />
        </HStack>

        <Box flex="1" overflowY="auto" borderWidth={1} borderRadius="md" p={4}>
          {messages.map((msg, idx) => (
            <Flex
              key={idx}
              mb={4}
              flexDirection={msg.role === 'user' ? 'row-reverse' : 'row'}
            >
              <Box
                maxW="80%"
                bg={msg.role === 'user' ? 'blue.100' : 'gray.100'}
                p={3}
                borderRadius="lg"
              >
                <Text whiteSpace="pre-wrap">{msg.content}</Text>
              </Box>
            </Flex>
          ))}
          <div ref={messagesEndRef} />
        </Box>
        
        <Flex>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="輸入您的問題..."
            mr={2}
            disabled={isProcessing}
          />
          <ButtonGroup>
            <Button 
              colorScheme="blue" 
              onClick={sendMessage}
              isDisabled={isProcessing}
            >
              發送
            </Button>
            <Button 
              colorScheme="red" 
              onClick={handleStop}
              isDisabled={!isProcessing}
            >
              中止
            </Button>
          </ButtonGroup>
        </Flex>
      </VStack>
    </Container>
  )
}

export default App
