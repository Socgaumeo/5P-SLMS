// frontend/src/hooks/useChatSession.js
import { useState, useRef, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const STORAGE_KEY = 'slms_chat_session_id'
const MESSAGES_KEY = 'slms_chat_messages'
const STATE_KEY = 'slms_chat_state'

export const useChatSession = () => {
    const [messages, setMessages] = useState([])
    const [sessionId, setSessionId] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [taskState, setTaskState] = useState('idle') // idle, collecting, confirming, executed
    const [confirmationData, setConfirmationData] = useState(null)
    const [intent, setIntent] = useState(null)
    const [accumulatedEntities, setAccumulatedEntities] = useState({})

    // Initialize session and restore messages
    useEffect(() => {
        const savedSession = localStorage.getItem(STORAGE_KEY)
        const savedMessages = localStorage.getItem(MESSAGES_KEY)
        const savedState = localStorage.getItem(STATE_KEY)

        if (savedSession) {
            setSessionId(savedSession)
            // Optionally fetch session state from server
            fetchSessionState(savedSession)
        }

        // Restore messages from localStorage
        if (savedMessages) {
            try {
                const parsed = JSON.parse(savedMessages)
                if (Array.isArray(parsed)) {
                    setMessages(parsed)
                }
            } catch (e) {
                console.error("Failed to parse saved messages", e)
            }
        }

        // Restore state
        if (savedState) {
            try {
                const state = JSON.parse(savedState)
                if (state.taskState) setTaskState(state.taskState)
                if (state.intent) setIntent(state.intent)
                if (state.accumulatedEntities) setAccumulatedEntities(state.accumulatedEntities)
            } catch (e) {
                console.error("Failed to parse saved state", e)
            }
        }
    }, [])

    // Save messages to localStorage whenever they change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages))
        }
    }, [messages])

    // Save state to localStorage
    useEffect(() => {
        const state = { taskState, intent, accumulatedEntities }
        localStorage.setItem(STATE_KEY, JSON.stringify(state))
    }, [taskState, intent, accumulatedEntities])

    const fetchSessionState = async (sid) => {
        try {
            const res = await fetch(`${API_URL}/api/chat/session/${sid}`)
            if (res.ok) {
                const data = await res.json()
                setTaskState(data.task_state)
                setIntent(data.intent)
                if (data.task_state === 'confirming') {
                    setConfirmationData(data.entities)
                }
                if (data.entities) {
                    setAccumulatedEntities(data.entities)
                }
            }
        } catch (e) {
            console.error("Failed to fetch session state", e)
        }
    }

    const sendMessage = async (content, file = null, context = {}) => {
        setIsLoading(true)

        // Debug: Log session info before sending
        console.log('[CHAT] sendMessage called')
        console.log('[CHAT] Current sessionId:', sessionId)
        console.log('[CHAT] Message:', content?.substring(0, 50) + '...')

        // Add user message immediately
        const userMsg = {
            id: Date.now().toString(),
            role: 'user',
            content: content || (file ? `File: ${file.name}` : ''),
            timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, userMsg])

        try {
            let result

            if (file) {
                const formData = new FormData()
                if (file.type.startsWith('image/')) {
                    formData.append('image', file)
                    formData.append('context', JSON.stringify({ ...context, session_id: sessionId }))
                    console.log('[CHAT] Sending image, session_id in context:', sessionId)
                    const res = await fetch(`${API_URL}/api/chat/process-image`, { method: 'POST', body: formData })
                    result = await res.json()
                } else {
                    formData.append('file', file)
                    formData.append('context', JSON.stringify({ ...context, session_id: sessionId }))
                    console.log('[CHAT] Sending file, session_id in context:', sessionId)
                    const res = await fetch(`${API_URL}/api/chat/process-file`, { method: 'POST', body: formData })
                    result = await res.json()
                }
            } else {
                console.log('[CHAT] Sending text message with session_id:', sessionId)
                const res = await fetch(`${API_URL}/api/chat/message`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: content,
                        session_id: sessionId,
                        context
                    })
                })
                result = await res.json()
                console.log('[CHAT] Response received, server session_id:', result.session_id, 'task_state:', result.task_state)
            }

            // Update session ID if new
            if (result.session_id && result.session_id !== sessionId) {
                setSessionId(result.session_id)
                localStorage.setItem(STORAGE_KEY, result.session_id)
            }

            // Add bot response
            const botMsg = {
                id: Date.now().toString() + '_bot',
                role: 'assistant',
                content: result.response,
                timestamp: new Date().toISOString(),
                needsConfirmation: result.needs_confirmation,
                confirmationData: result.confirmation_data,
                intent: result.intent
            }
            setMessages(prev => [...prev, botMsg])

            // Update state
            if (result.task_state) setTaskState(result.task_state)
            setConfirmationData(result.confirmation_data)
            setIntent(result.intent)
            if (result.accumulated_entities) setAccumulatedEntities(result.accumulated_entities)

            return result

        } catch (error) {
            console.error("Chat error:", error)
            setMessages(prev => [...prev, {
                id: Date.now().toString() + '_err',
                role: 'assistant',
                content: "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.",
                isError: true
            }])
        } finally {
            setIsLoading(false)
        }
    }

    const confirmAction = async () => {
        if (!sessionId) return

        setIsLoading(true)
        try {
            const res = await fetch(`${API_URL}/api/chat/confirm/${sessionId}`, { method: 'POST' })
            const result = await res.json()

            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'user',
                content: 'OK',
                timestamp: new Date().toISOString()
            }, {
                id: Date.now().toString() + '_bot',
                role: 'assistant',
                content: result.response,
                timestamp: new Date().toISOString()
            }])

            setTaskState('idle')
            setConfirmationData(null)

            return result
        } catch (error) {
            console.error("Confirm error:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const cancelTask = async () => {
        if (!sessionId) return

        setIsLoading(true)
        try {
            const res = await fetch(`${API_URL}/api/chat/cancel/${sessionId}`, { method: 'POST' })
            const result = await res.json()

            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'user',
                content: 'Hủy',
                timestamp: new Date().toISOString()
            }, {
                id: Date.now().toString() + '_bot',
                role: 'assistant',
                content: result.response,
                timestamp: new Date().toISOString()
            }])

            setTaskState('idle')
            setConfirmationData(null)
        } catch (error) {
            console.error("Cancel error:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const clearSession = () => {
        setSessionId(null)
        setMessages([])
        setTaskState('idle')
        setConfirmationData(null)
        setIntent(null)
        setAccumulatedEntities({})
        localStorage.removeItem(STORAGE_KEY)
        localStorage.removeItem(MESSAGES_KEY)
        localStorage.removeItem(STATE_KEY)
    }

    return {
        messages,
        sessionId,
        isLoading,
        taskState,
        confirmationData,
        intent,
        accumulatedEntities,
        sendMessage,
        confirmAction,
        cancelTask,
        clearSession
    }
}
