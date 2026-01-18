export interface BrainStats {
    thoughts: number;
    entities: number;
    categories: number;
    pending_actions: number;
}

export interface RecentThought {
    id: string;
    content: string;
    summary: string;
    timestamp: string;
    categories: string[];
}

export interface ActiveProject {
    name: string;
    description: string;
    status: string;
    updates: number;
    last_update: string;
}

export interface UpcomingEvent {
    id: string;
    title: string;
    datetime: string;
    priority: string;
}

export interface PersonProfile {
    name: string;
    description: string;
    mentions: number;
    last_seen: string;
}

export interface DashboardData {
    user_id: string;
    stats: BrainStats;
    recent_thoughts: RecentThought[];
    active_projects: ActiveProject[];
    upcoming_events: UpcomingEvent[];
    recent_people: PersonProfile[];
}
