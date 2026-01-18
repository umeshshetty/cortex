import type { ActiveProject } from '../../types/dashboard';

interface ProjectsWidgetProps {
    projects: ActiveProject[];
}

export function ProjectsWidget({ projects }: ProjectsWidgetProps) {
    return (
        <div className="dashboard-widget projects-widget">
            <h3>Active Projects</h3>
            {(!projects || projects.length === 0) ? (
                <p className="empty-state">No active projects.</p>
            ) : (
                <div className="projects-list">
                    {projects.map((project) => (
                        <div key={project.name} className="project-item">
                            <div className="project-header">
                                <span className="project-name">{project.name}</span>
                                <span className={`status-dot ${project.status || 'active'}`}></span>
                            </div>
                            <p className="project-desc">{project.description || 'No description'}</p>
                            <div className="project-meta">
                                <span>{project.updates} updates</span>
                                <span>Last: {new Date(project.last_update).toLocaleDateString()}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
