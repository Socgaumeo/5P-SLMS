// frontend/src/components/chat/ChatWindow.jsx
import React, { useState, useRef, useEffect } from 'react'
import { useChatSession } from '../../hooks/useChatSession'
import EntityCard from './EntityCard'
import MessageContent from './MessageContent'

const ChatWindow = ({ isOpen, onClose }) => {
    const {
        messages,
        isLoading,
        sendMessage,
        confirmAction,
        cancelTask,
        taskState,
        confirmationData,
        intent,
        accumulatedEntities
    } = useChatSession()

    const [input, setInput] = useState('')
    const [isDragging, setIsDragging] = useState(false)
    const [attachedFile, setAttachedFile] = useState(null)

    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)
    const fileInputRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    useEffect(() => {
        if (isOpen) {
            scrollToBottom()
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [isOpen])

    // ESC key to close
    useEffect(() => {
        if (!isOpen) return
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') onClose()
        }
        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen, onClose])

    const handleSend = async () => {
        if ((!input.trim() && !attachedFile) || isLoading) return

        await sendMessage(input, attachedFile)

        setInput('')
        setAttachedFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const handleFileSelect = (file) => {
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/pdf',
            'image/png', 'image/jpeg', 'image/jpg'
        ]
        if (!allowedTypes.includes(file.type)) {
            alert('Chỉ hỗ trợ file Excel, PDF hoặc ảnh (PNG/JPG)')
            return
        }
        setAttachedFile(file)
    }

    if (!isOpen) return null

    return (
        <div className={`chat-window ${isOpen ? 'open' : ''}`}>
            <div className="chat-header">
                <div className="chat-title">
                    <span>🤖 5P Assistant</span>
                    <span className={`status-dot ${isLoading ? 'thinking' : 'active'}`}></span>
                </div>
                <div className="chat-controls">
                    <button className="chat-close" onClick={onClose} title="Đóng (ESC)">✕</button>
                </div>
            </div>

            <div
                className={`chat-messages ${isDragging ? 'dragging' : ''}`}
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={e => { e.preventDefault(); setIsDragging(false) }}
                onDrop={e => {
                    e.preventDefault();
                    setIsDragging(false);
                    if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0])
                }}
            >
                {messages.length === 0 && (
                    <div className="empty-state">
                        <p>Xin chào! Tôi có thể giúp gì cho bạn?</p>
                        <div className="suggestion-chips">
                            <button onClick={() => sendMessage("Đặt xe cho DRT1 ngày mai")}>Booking mới</button>
                            <button onClick={() => sendMessage("Job JOB123 đi đến đâu rồi?")}>Tra cứu Job</button>
                            <button onClick={() => sendMessage("Gán xe cho job JOB456")}>Gán xe</button>
                        </div>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className={`message-bubble ${msg.role} ${msg.isError ? 'error' : ''}`}>
                            <div className="message-content">
                                <MessageContent content={msg.content} />
                            </div>
                        </div>
                        <div className="message-time">
                            {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </div>
                    </div>
                ))}

                {/* Show EntityCard when we have accumulated entities */}
                {accumulatedEntities && Object.keys(accumulatedEntities).length > 0 && (taskState === 'collecting' || taskState === 'confirming') && (
                    <EntityCard
                        entities={accumulatedEntities}
                        intent={intent}
                        onConfirm={confirmAction}
                        onCancel={cancelTask}
                        onEdit={(editedEntities) => {
                            const editMsg = Object.entries(editedEntities)
                                .filter(([k, v]) => v !== accumulatedEntities[k])
                                .map(([k, v]) => `${k}: ${v}`)
                                .join(', ')
                            if (editMsg) sendMessage(`Sửa: ${editMsg}`)
                        }}
                        isLoading={isLoading}
                    />
                )}

                {isLoading && (
                    <div className="message assistant loading">
                        <div className="typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                {attachedFile && (
                    <div className="attached-file-preview">
                        <span>📎 {attachedFile.name}</span>
                        <button onClick={() => setAttachedFile(null)}>✕</button>
                    </div>
                )}
                <div className="input-row">
                    <button className="btn-attach" onClick={() => fileInputRef.current?.click()} title="Đính kèm file">
                        📎
                    </button>
                    <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    />
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={e => {
                            setInput(e.target.value)
                            // Auto-grow logic
                            e.target.style.height = 'auto'
                            e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
                        }}
                        onKeyDown={handleKeyDown}
                        placeholder="Nhập tin nhắn... (hoặc kéo thả file Excel, PDF, ảnh)"
                        rows={1}
                        style={{ minHeight: '48px' }}
                    />
                    <button className="btn-send" onClick={handleSend} disabled={isLoading || (!input && !attachedFile)}>
                        ➤
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ChatWindow

