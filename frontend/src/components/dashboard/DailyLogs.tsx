import type { RecentThought } from '../../types/dashboard';

interface DailyLogsProps {
    logs: RecentThought[];
}

export function DailyLogs({ logs }: DailyLogsProps) {
    if (!logs?.length) {
        return (
            <div className="dashboard-widget daily-logs empty">
                <h3>Daily Logs</h3>
                <p className="empty-state">No recent thoughts recorded.</p>
            </div>
        );
    }

    return (
        <div className="dashboard-widget daily-logs">
            <h3>Daily Logs</h3>
            <div className="logs-list">
                {logs.map((log) => (
                    <div key={log.id} className="log-entry">
                        <div className="log-header">
                            <span className="log-time">
                                {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            {log.categories?.map(cat => (
                                <span key={cat} className="log-category">{cat}</span>
                            ))}
                        </div>
                        <p className="log-summary">{log.summary || log.content}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
