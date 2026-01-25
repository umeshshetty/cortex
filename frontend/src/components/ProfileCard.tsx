import { useState, useEffect } from 'react';
import { api, type UserProfile } from '../api';
import './ProfileCard.css';

export function ProfileCard() {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [editing, setEditing] = useState(false);
    const [form, setForm] = useState({ name: '', role: '', bio: '', traits: '' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProfile();
    }, []);

    async function loadProfile() {
        setLoading(true);
        const data = await api.getProfile();
        if (data) {
            setProfile(data);
            setForm({
                name: data.name || '',
                role: data.role || '',
                bio: data.bio || '',
                traits: data.traits?.join(', ') || '',
            });
        }
        setLoading(false);
    }

    async function handleSave() {
        const saved = await api.saveProfile({
            name: form.name,
            role: form.role || undefined,
            bio: form.bio || undefined,
            traits: form.traits ? form.traits.split(',').map(t => t.trim()) : [],
        });
        setProfile(saved);
        setEditing(false);
    }

    if (loading) {
        return (
            <div className="profile-card glass-card">
                <div className="profile-loading animate-pulse">Loading...</div>
            </div>
        );
    }

    return (
        <div className="profile-card glass-card animate-fade-in">
            <div className="profile-header">
                <div className="profile-avatar">
                    {(profile?.name || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="profile-info">
                    {editing ? (
                        <input
                            className="input profile-name-input"
                            value={form.name}
                            onChange={e => setForm({ ...form, name: e.target.value })}
                            placeholder="Your name"
                        />
                    ) : (
                        <h2 className="profile-name">{profile?.name || 'Set up your profile'}</h2>
                    )}
                    {editing ? (
                        <input
                            className="input profile-role-input"
                            value={form.role}
                            onChange={e => setForm({ ...form, role: e.target.value })}
                            placeholder="Your role"
                        />
                    ) : (
                        <p className="profile-role">{profile?.role || 'Click edit to get started'}</p>
                    )}
                </div>
                <button
                    className={`btn ${editing ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={editing ? handleSave : () => setEditing(true)}
                >
                    {editing ? 'Save' : 'Edit'}
                </button>
            </div>

            {editing && (
                <div className="profile-edit-fields">
                    <label className="label">Bio</label>
                    <textarea
                        className="input textarea"
                        value={form.bio}
                        onChange={e => setForm({ ...form, bio: e.target.value })}
                        placeholder="Tell me about yourself..."
                    />
                    <label className="label">Traits (comma separated)</label>
                    <input
                        className="input"
                        value={form.traits}
                        onChange={e => setForm({ ...form, traits: e.target.value })}
                        placeholder="Curious, Builder, ..."
                    />
                </div>
            )}

            {!editing && profile?.bio && (
                <p className="profile-bio">{profile.bio}</p>
            )}

            {!editing && profile?.traits && profile.traits.length > 0 && (
                <div className="profile-traits">
                    {profile.traits.map((trait, i) => (
                        <span key={i} className="tag">{trait}</span>
                    ))}
                </div>
            )}
        </div>
    );
}
