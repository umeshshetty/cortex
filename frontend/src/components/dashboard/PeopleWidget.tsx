import type { PersonProfile } from '../../types/dashboard';

interface PeopleWidgetProps {
    people: PersonProfile[];
}

export function PeopleWidget({ people }: PeopleWidgetProps) {
    return (
        <div className="dashboard-widget people-widget">
            <h3>Recent People</h3>
            {(!people || people.length === 0) ? (
                <p className="empty-state">No recent interactions.</p>
            ) : (
                <div className="people-grid">
                    {people.map((person) => (
                        <div key={person.name} className="person-card">
                            <div className="person-avatar">{person.name.charAt(0)}</div>
                            <div className="person-info">
                                <span className="person-name">{person.name}</span>
                                <span className="person-role">{person.description.split('|')[0] || 'Contact'}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
