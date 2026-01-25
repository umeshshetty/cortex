import { useState, useEffect } from 'react';
import { api, type Note } from '../api';
import './MemoryStream.css';

interface Props {
    refreshTrigger?: number;
}

export function MemoryStream({ refreshTrigger }: Props) {
    const [notes, setNotes] = useState<Note[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadNotes();
    }, [refreshTrigger]);

    async function loadNotes() {
        setLoading(true);
        const data = await api.getStream(20);
        setNotes(data);
        setLoading(false);
    }

    function formatTime(timestamp: string) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    if (loading) {
        return (
            <div className="memory-stream glass-card">
                <div className="stream-header">
                    <span className="stream-icon">🧠</span>
                    <span className="stream-title">Memory Stream</span>
                </div>
                <div className="stream-loading animate-pulse">Loading memories...</div>
            </div>
        );
    }

    return (
        <div className="memory-stream glass-card animate-fade-in">
            <div className="stream-header">
                <span className="stream-icon">🧠</span>
                <span className="stream-title">Memory Stream</span>
                <span className="stream-count">{notes.length} entries</span>
            </div>

            {notes.length === 0 ? (
                <div className="stream-empty">
                    <p>No memories yet. Start capturing your thoughts above!</p>
                </div>
            ) : (
                <div className="stream-list">
                    {notes.map((note, i) => (
                        <div key={note.id} className="stream-item" style={{ animationDelay: `${i * 0.05}s` }}>
                            <div className="stream-item-content">{note.content}</div>
                            <div className="stream-item-meta">
                                <span className="stream-item-time">{formatTime(note.timestamp)}</span>
                                <span className="stream-item-source">{note.source}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
