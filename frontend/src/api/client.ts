import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface ThoughtRequest {
  thought: string;
}

export interface Entity {
  name: string;
  type: string;
  description?: string;
}

export interface ThoughtResponse {
  thought_id: string;
  response: string;
  analysis?: string;
  entities: Entity[];
  categories: { name: string; confidence: number }[];
  summary?: string;
  route?: string;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  data?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface BrainStats {
  thoughts: number;
  entities: number;
  categories: number;
  pending_actions: number;
}

// API Functions
export const processThought = async (thought: string): Promise<ThoughtResponse> => {
  const response = await api.post<ThoughtResponse>('/api/think', { thought });
  return response.data;
};

export const getGraph = async (): Promise<GraphData> => {
  const response = await api.get<GraphData>('/api/graph');
  return response.data;
};

export const getBrainStats = async (): Promise<BrainStats> => {
  const response = await api.get<BrainStats>('/api/brain/stats');
  return response.data;
};

export const searchThoughts = async (query: string) => {
  const response = await api.get(`/api/brain/search?q=${encodeURIComponent(query)}`);
  return response.data;
};

export const getPeople = async () => {
  const response = await api.get('/api/brain/people');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};
