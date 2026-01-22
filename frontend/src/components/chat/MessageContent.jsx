import React, { useState } from 'react';
import './MessageContent.css';

/**
 * MessageContent component renders chat messages with:
 * - Line break handling
 * - Code block rendering with copy button
 * - Bold text support (**text**)
 */
export default function MessageContent({ content }) {
    const [copiedIndex, setCopiedIndex] = useState(null);

    if (!content) return null;

    // Split content by code blocks (```...```)
    const parts = content.split(/(```[\s\S]*?```)/g);

    const handleCopy = (text, index) => {
        // Remove the ``` markers
        const cleanText = text.replace(/^```\n?/, '').replace(/\n?```$/, '');
        navigator.clipboard.writeText(cleanText).then(() => {
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        });
    };

    const renderPart = (part, index) => {
        // Check if this is a code block
        if (part.startsWith('```') && part.endsWith('```')) {
            const codeContent = part.replace(/^```\n?/, '').replace(/\n?```$/, '');
            return (
                <div key={index} className="code-block-container">
                    <pre className="code-block">
                        {codeContent}
                    </pre>
                    <button
                        className={`copy-button ${copiedIndex === index ? 'copied' : ''}`}
                        onClick={() => handleCopy(part, index)}
                        title="Copy to clipboard"
                    >
                        {copiedIndex === index ? '✓ Đã copy' : '📋 Copy'}
                    </button>
                </div>
            );
        }

        // Regular text - handle line breaks and bold
        return (
            <span key={index}>
                {part.split('\n').map((line, lineIdx) => (
                    <React.Fragment key={lineIdx}>
                        {lineIdx > 0 && <br />}
                        {renderLine(line)}
                    </React.Fragment>
                ))}
            </span>
        );
    };

    const renderLine = (line) => {
        // Handle **bold** text
        const boldParts = line.split(/(\*\*[^*]+\*\*)/g);
        return boldParts.map((part, idx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={idx}>{part.slice(2, -2)}</strong>;
            }
            return <span key={idx}>{part}</span>;
        });
    };

    return (
        <div className="formatted-message">
            {parts.map((part, index) => renderPart(part, index))}
        </div>
    );
}
