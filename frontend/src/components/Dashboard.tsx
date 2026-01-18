import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useAgent } from '../hooks/useAgent';
import { DailyLogs } from './dashboard/DailyLogs';
import { ProjectsWidget } from './dashboard/ProjectsWidget';
import { PeopleWidget } from './dashboard/PeopleWidget';
import { CalendarWidget } from './dashboard/CalendarWidget';
import type { DashboardData } from '../types/dashboard';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function Dashboard() {
    const [input, setInput] = useState('');
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const { think, isThinking, lastResponse } = useAgent();

    const fetchDashboardData = async () => {
        try {
            const res = await fetch(`${API_URL}/api/dashboard/command-center?user_id=user_123`);
            if (res.ok) {
                const data = await res.json();
                setDashboardData(data);
            }
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        }
    };

    useEffect(() => {
        fetchDashboardData();
        // Refresh every 30s
        const interval = setInterval(fetchDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        await think(input);
        setInput('');
        // Refresh data after thinking (might have created new thoughts/actions)
        setTimeout(fetchDashboardData, 2000);
    };

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <div className="logo">
                    <span className="logo-icon">🧠</span>
                    <h1>Cortex</h1>
                </div>
                <div className="stats-bar">
                    <div className="stat-item">
                        <span className="stat-value">{dashboardData?.stats.thoughts ?? 0}</span>
                        <span className="stat-label">Thoughts</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{dashboardData?.stats.entities ?? 0}</span>
                        <span className="stat-label">Entities</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{dashboardData?.stats.pending_actions ?? 0}</span>
                        <span className="stat-label">Actions</span>
                    </div>
                </div>
            </header>

            {/* Left Column */}
            <div className="dashboard-left">
                <DailyLogs logs={dashboardData?.recent_thoughts || []} />
                <ProjectsWidget projects={dashboardData?.active_projects || []} />
            </div>

            {/* Center Column: Chat/Think */}
            <div className="dashboard-center">
                <div className="thought-input-container">
                    <form className="thought-input" onSubmit={handleSubmit}>
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="What's on your mind?"
                            rows={3}
                            disabled={isThinking}
                        />
                        <div className="action-bar">
                            <button type="submit" className="think-btn" disabled={isThinking || !input.trim()}>
                                {isThinking ? 'Thinking...' : 'Think'}
                            </button>
                        </div>
                    </form>
                </div>

                <div className="response-feed">
                    {lastResponse && (
                        <div className="response-card">
                            <div className="response-header">
                                <span className="route-badge">{lastResponse.route}</span>
                                {lastResponse.thought_id && (
                                    <span className="thought-id">#{lastResponse.thought_id.slice(0, 8)}</span>
                                )}
                            </div>

                            <div className="response-content">
                                <p>{lastResponse.response}</p>
                            </div>

                            {lastResponse.entities.length > 0 && (
                                <div className="entities-section">
                                    <h4>Extracted Entities</h4>
                                    <div className="entity-tags">
                                        {lastResponse.entities.map((entity, i) => (
                                            <span key={i} className={`entity-tag entity-${entity.type.toLowerCase()}`}>
                                                {entity.name}
                                                <span className="entity-type">{entity.type}</span>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Right Column */}
            <div className="dashboard-right">
                <CalendarWidget events={dashboardData?.upcoming_events || []} />
                <PeopleWidget people={dashboardData?.recent_people || []} />
            </div>
        </div>
    );
}
