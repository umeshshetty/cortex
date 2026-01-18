import { useEffect, useRef, useState } from 'react';
import { useGraph } from '../hooks/useAgent';
import './GraphVisualizer.css';

interface Position {
    x: number;
    y: number;
}

export function GraphVisualizer() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const { data: graphData, isLoading } = useGraph();
    const [nodePositions, setNodePositions] = useState<Map<string, Position>>(new Map());
    const [selectedNode, setSelectedNode] = useState<string | null>(null);

    // Initialize node positions with force-directed layout simulation
    useEffect(() => {
        if (!graphData?.nodes.length) return;

        const positions = new Map<string, Position>();
        const width = 800;
        const height = 600;
        const centerX = width / 2;
        const centerY = height / 2;

        // Simple circular layout with some randomness
        graphData.nodes.forEach((node, i) => {
            const angle = (i / graphData.nodes.length) * 2 * Math.PI;
            const radius = 150 + Math.random() * 100;
            positions.set(node.id, {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
            });
        });

        setNodePositions(positions);
    }, [graphData]);

    // Draw the graph
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !graphData) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear canvas
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw edges
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 1;
        graphData.edges.forEach((edge) => {
            const source = nodePositions.get(edge.source);
            const target = nodePositions.get(edge.target);
            if (source && target) {
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();
            }
        });

        // Draw nodes
        graphData.nodes.forEach((node) => {
            const pos = nodePositions.get(node.id);
            if (!pos) return;

            const radius = node.type === 'Thought' ? 8 : 12;
            const isSelected = selectedNode === node.id;

            // Node color based on type
            const colors: Record<string, string> = {
                Thought: '#6366f1',
                Person: '#3b82f6',
                Project: '#a855f7',
                Topic: '#22c55e',
                Entity: '#f59e0b',
            };

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = colors[node.type] || '#64748b';
            ctx.fill();

            if (isSelected) {
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Label
            ctx.fillStyle = '#e2e8f0';
            ctx.font = '10px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(node.label.slice(0, 15), pos.x, pos.y + radius + 12);
        });
    }, [graphData, nodePositions, selectedNode]);

    // Handle click
    const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas || !graphData) return;

        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Find clicked node
        for (const node of graphData.nodes) {
            const pos = nodePositions.get(node.id);
            if (!pos) continue;

            const dx = x - pos.x;
            const dy = y - pos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 15) {
                setSelectedNode(node.id === selectedNode ? null : node.id);
                return;
            }
        }
        setSelectedNode(null);
    };

    if (isLoading) {
        return (
            <div className="graph-loading">
                <div className="loading-spinner"></div>
                <p>Loading knowledge graph...</p>
            </div>
        );
    }

    const selectedNodeData = graphData?.nodes.find((n) => n.id === selectedNode);

    return (
        <div className="graph-visualizer">
            <div className="graph-header">
                <h2>Knowledge Graph</h2>
                <p>{graphData?.nodes.length || 0} nodes · {graphData?.edges.length || 0} connections</p>
            </div>

            <div className="graph-container">
                <canvas
                    ref={canvasRef}
                    width={800}
                    height={600}
                    onClick={handleClick}
                />

                {selectedNodeData && (
                    <div className="node-details">
                        <h3>{selectedNodeData.label}</h3>
                        <span className="node-type">{selectedNodeData.type}</span>
                        {selectedNodeData.data && (
                            <pre>{JSON.stringify(selectedNodeData.data, null, 2)}</pre>
                        )}
                    </div>
                )}
            </div>

            <div className="graph-legend">
                <div className="legend-item">
                    <span className="legend-dot thought"></span> Thought
                </div>
                <div className="legend-item">
                    <span className="legend-dot person"></span> Person
                </div>
                <div className="legend-item">
                    <span className="legend-dot project"></span> Project
                </div>
                <div className="legend-item">
                    <span className="legend-dot topic"></span> Topic
                </div>
            </div>
        </div>
    );
}
