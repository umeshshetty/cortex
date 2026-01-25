import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, system-ui, sans-serif',
});

interface Props {
    chart: string;
}

export function MermaidDiagram({ chart }: Props) {
    const ref = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState('');

    useEffect(() => {
        if (ref.current) {
            mermaid.render(`mermaid-${Math.random().toString(36).substr(2, 9)}`, chart).then(({ svg }) => {
                setSvg(svg);
            });
        }
    }, [chart]);

    return (
        <div
            ref={ref}
            className="mermaid-wrapper"
            dangerouslySetInnerHTML={{ __html: svg }}
            style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0', overflowX: 'auto' }}
        />
    );
}
