import { useQuery, useQueryClient } from '@tanstack/react-query';
import { processThought, getBrainStats, getGraph, searchThoughts, type ThoughtResponse } from '../api/client';
import { useState, useCallback } from 'react';

/**
 * Hook for processing thoughts through the agent.
 */
export function useAgent() {
    const queryClient = useQueryClient();
    const [isThinking, setIsThinking] = useState(false);
    const [lastResponse, setLastResponse] = useState<ThoughtResponse | null>(null);
    const [error, setError] = useState<Error | null>(null);

    const think = useCallback(async (thought: string) => {
        setIsThinking(true);
        setError(null);

        try {
            const response = await processThought(thought);
            setLastResponse(response);
            // Invalidate relevant queries
            queryClient.invalidateQueries({ queryKey: ['brainStats'] });
            queryClient.invalidateQueries({ queryKey: ['graph'] });
            return response;
        } catch (err) {
            console.error('Think error:', err);
            setError(err as Error);
            throw err;
        } finally {
            setIsThinking(false);
        }
    }, [queryClient]);

    return {
        think,
        isThinking,
        lastResponse,
        error,
        reset: () => {
            setLastResponse(null);
            setError(null);
        },
    };
}

/**
 * Hook for brain statistics.
 */
export function useBrainStats() {
    return useQuery({
        queryKey: ['brainStats'],
        queryFn: getBrainStats,
        staleTime: 30000, // 30 seconds
        retry: 1,
        refetchOnWindowFocus: false,
    });
}

/**
 * Hook for knowledge graph data.
 */
export function useGraph() {
    return useQuery({
        queryKey: ['graph'],
        queryFn: getGraph,
        staleTime: 60000, // 1 minute
        retry: 1,
        refetchOnWindowFocus: false,
    });
}

/**
 * Hook for semantic search.
 */
export function useSearch(query: string, enabled = true) {
    return useQuery({
        queryKey: ['search', query],
        queryFn: () => searchThoughts(query),
        enabled: enabled && query.length > 2,
        staleTime: 60000,
    });
}

