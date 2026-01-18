import { useState } from 'react';
import './ClarificationQueue.css';

interface Clarification {
    id: string;
    question: string;
    context: string;
    options?: string[];
    timestamp: string;
}

interface ClarificationQueueProps {
    clarifications?: Clarification[];
    onRespond?: (id: string, response: string) => void;
    onDismiss?: (id: string) => void;
}

export function ClarificationQueue({
    clarifications = [],
    onRespond,
    onDismiss
}: ClarificationQueueProps) {
    const [responses, setResponses] = useState<Record<string, string>>({});

    const handleSubmit = (id: string) => {
        if (responses[id] && onRespond) {
            onRespond(id, responses[id]);
            setResponses((prev) => {
                const next = { ...prev };
                delete next[id];
                return next;
            });
        }
    };

    if (clarifications.length === 0) {
        return null;
    }

    return (
        <div className="clarification-queue">
            <div className="queue-header">
                <span className="queue-icon">❓</span>
                <h3>Clarification Needed</h3>
                <span className="queue-count">{clarifications.length}</span>
            </div>

            <div className="queue-items">
                {clarifications.map((item) => (
                    <div key={item.id} className="clarification-card">
                        <div className="clarification-content">
                            <p className="clarification-question">{item.question}</p>
                            {item.context && (
                                <p className="clarification-context">{item.context}</p>
                            )}
                        </div>

                        {item.options ? (
                            <div className="clarification-options">
                                {item.options.map((option, i) => (
                                    <button
                                        key={i}
                                        onClick={() => onRespond?.(item.id, option)}
                                        className="option-button"
                                    >
                                        {option}
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="clarification-input">
                                <input
                                    type="text"
                                    placeholder="Your response..."
                                    value={responses[item.id] || ''}
                                    onChange={(e) =>
                                        setResponses((prev) => ({
                                            ...prev,
                                            [item.id]: e.target.value,
                                        }))
                                    }
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') handleSubmit(item.id);
                                    }}
                                />
                                <button onClick={() => handleSubmit(item.id)}>Send</button>
                            </div>
                        )}

                        <button
                            className="dismiss-button"
                            onClick={() => onDismiss?.(item.id)}
                            title="Dismiss"
                        >
                            ×
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
