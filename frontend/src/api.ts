const API_BASE = 'http://localhost:8000';

export interface UserProfile {
  id: string;
  name: string;
  role?: string;
  bio?: string;
  traits: string[];
  created_at?: string;
  updated_at?: string;
}

export interface Note {
  id: number;
  content: string;
  timestamp: string;
  source: string;
}

export const api = {
  // Profile
  async getProfile(): Promise<UserProfile | null> {
    try {
      const res = await fetch(`${API_BASE}/api/profile`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  },

  async saveProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/api/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    return res.json();
  },

  // Memory
  async addNote(content: string): Promise<Note> {
    const res = await fetch(`${API_BASE}/api/memory/note`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    return res.json();
  },

  async getStream(limit = 20): Promise<Note[]> {
    const res = await fetch(`${API_BASE}/api/memory/stream?limit=${limit}`);
    return res.json();
  },

  // Health
  async health(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },
};
