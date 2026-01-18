import type { UpcomingEvent } from '../../types/dashboard';

interface CalendarWidgetProps {
    events: UpcomingEvent[];
}

export function CalendarWidget({ events }: CalendarWidgetProps) {
    return (
        <div className="dashboard-widget calendar-widget">
            <h3>Upcoming</h3>
            {(!events || events.length === 0) ? (
                <p className="empty-state">No upcoming events.</p>
            ) : (
                <div className="events-list">
                    {events.map((event) => (
                        <div key={event.id} className="event-item">
                            <div className="event-date">
                                <span className="day">{new Date(event.datetime).getDate()}</span>
                                <span className="month">{new Date(event.datetime).toLocaleString('default', { month: 'short' })}</span>
                            </div>
                            <div className="event-details">
                                <span className="event-title">{event.title}</span>
                                <span className="event-time">
                                    {new Date(event.datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
