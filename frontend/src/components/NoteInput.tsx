import { useState } from 'react';
import { api } from '../api';
import './NoteInput.css';

interface Props {
    onNoteAdded?: () => void;
}

export function NoteInput({ onNoteAdded }: Props) {
    const [content, setContent] = useState('');
    const [sending, setSending] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!content.trim() || sending) return;

        setSending(true);
        try {
            await api.addNote(content.trim());
            setContent('');
            onNoteAdded?.();
        } finally {
            setSending(false);
        }
    }

    return (
        <form className="note-input glass-card" onSubmit={handleSubmit}>
            <div className="note-input-header">
                <span className="note-input-icon">💭</span>
                <span className="note-input-label">Capture a thought</span>
            </div>
            <textarea
                className="input textarea note-textarea"
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="What's on your mind? Ideas, notes, thoughts..."
                onKeyDown={e => {
                    if (e.key === 'Enter' && e.metaKey) {
                        handleSubmit(e);
                    }
                }}
            />
            <div className="note-input-footer">
                <span className="note-input-hint">⌘ + Enter to save</span>
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!content.trim() || sending}
                >
                    {sending ? 'Saving...' : 'Save to Brain'}
                </button>
            </div>
        </form>
    );
}
