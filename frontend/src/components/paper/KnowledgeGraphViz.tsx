import React, { useEffect, useRef, useState } from 'react';
import { Box, IconButton, Paper, Tooltip, Typography, Chip, Stack, Slider } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import RemoveRoundedIcon from '@mui/icons-material/RemoveRounded';
import RestartAltRoundedIcon from '@mui/icons-material/RestartAltRounded';
import OpenWithRoundedIcon from '@mui/icons-material/OpenWithRounded';
import FilterCenterFocusRoundedIcon from '@mui/icons-material/FilterCenterFocusRounded';
import * as d3 from 'd3';
import { KnowledgeGraph } from '../../types';

interface KnowledgeGraphVizProps {
  data: KnowledgeGraph;
}

const GRAPH_HEIGHT = 500;
const MIN_ZOOM = 0.35;
const MAX_ZOOM = 2.4;
const DEFAULT_ZOOM = 0.92;

export const KnowledgeGraphViz: React.FC<KnowledgeGraphVizProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const svgSelectionRef = useRef<d3.Selection<SVGSVGElement, unknown, null, undefined> | null>(null);
  const graphBoundsRef = useRef<{ minX: number; maxX: number; minY: number; maxY: number } | null>(null);
  const theme = useTheme();
  const [graphWidth, setGraphWidth] = useState(0);
  const [zoomPercent, setZoomPercent] = useState(100);

  useEffect(() => {
    if (!containerRef.current) return;

    const measure = () => {
      if (!containerRef.current) return;
      setGraphWidth(containerRef.current.clientWidth);
    };

    measure();

    const observer = new ResizeObserver(() => measure());
    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!svgRef.current || !data || !data.nodes?.length || !graphWidth) return;

    const width = graphWidth;
    const height = GRAPH_HEIGHT;
    let hasAutoFit = false;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('cursor', 'grab')
      .style('touch-action', 'none');

    svgSelectionRef.current = svg;

    const viewport = svg.append('g');

    const tooltip = d3.select('body')
      .append('div')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', theme.palette.mode === 'dark' ? 'rgba(8,17,31,0.92)' : 'rgba(255,255,255,0.96)')
      .style('color', theme.palette.text.primary)
      .style('padding', '8px')
      .style('border', `1px solid ${theme.palette.divider}`)
      .style('border-radius', '12px')
      .style('font-size', '12px')
      .style('max-width', '250px')
      .style('z-index', '1000');

    const colorScale = d3.scaleOrdinal<string>()
      .domain(['method', 'dataset', 'metric', 'concept'])
      .range([theme.palette.primary.main, theme.palette.secondary.main, theme.palette.warning.main, '#8b5cf6']);

    const simulation = d3.forceSimulation()
      .nodes(data.nodes as any)
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('link', d3.forceLink(data.edges as any).id((d: any) => d.id).distance(150))
      .force('collide', d3.forceCollide().radius(40));

    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([MIN_ZOOM, MAX_ZOOM])
      .translateExtent([[-width, -height], [width * 2, height * 2]])
      .on('start', () => {
        svg.style('cursor', 'grabbing');
      })
      .on('zoom', (event) => {
        viewport.attr('transform', event.transform.toString());
        setZoomPercent(Math.round(event.transform.k * 100));
      })
      .on('end', () => {
        svg.style('cursor', 'grab');
      });

    zoomBehaviorRef.current = zoomBehavior;
    svg.call(zoomBehavior).on('dblclick.zoom', null);

    const initialTransform = d3.zoomIdentity.translate(width * 0.08, height * 0.05).scale(DEFAULT_ZOOM);
    svg.call(zoomBehavior.transform, initialTransform);

    const links = viewport.selectAll('line')
      .data(data.edges)
      .enter()
      .append('line')
      .attr('stroke', theme.palette.divider)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6);

    const nodes = viewport.selectAll('circle')
      .data(data.nodes)
      .enter()
      .append('circle')
      .attr('r', (d: any) => Math.sqrt(d.value || 1) * 8 + 10)
      .attr('fill', (d: any) => colorScale(d.category))
      .attr('stroke', theme.palette.background.paper)
      .attr('stroke-width', 2)
      .call(d3.drag<SVGCircleElement, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    const labels = viewport.selectAll('text')
      .data(data.nodes)
      .enter()
      .append('text')
      .text((d: any) => d.label)
      .attr('font-size', '12px')
      .attr('fill', theme.palette.text.primary)
      .attr('text-anchor', 'middle')
      .attr('dy', (d: any) => Math.sqrt(d.value || 1) * 8 + 25);

    nodes
      .on('mouseover', (_event, d) => {
        tooltip.style('visibility', 'visible')
          .html(`<strong>${d.label}</strong><br/>${d.definition || 'No definition'}<br/><em>${d.category}</em>`);
      })
      .on('mousemove', (event) => {
        tooltip.style('top', (event.pageY - 10) + 'px')
          .style('left', (event.pageX + 10) + 'px');
      })
      .on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      });

    simulation.on('tick', () => {
      const positionedNodes = data.nodes.filter((node: any) => typeof node.x === 'number' && typeof node.y === 'number');
      if (positionedNodes.length) {
        graphBoundsRef.current = {
          minX: d3.min(positionedNodes, (node: any) => node.x) ?? 0,
          maxX: d3.max(positionedNodes, (node: any) => node.x) ?? width,
          minY: d3.min(positionedNodes, (node: any) => node.y) ?? 0,
          maxY: d3.max(positionedNodes, (node: any) => node.y) ?? height,
        };
      }

      links
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodes
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);

      if (!hasAutoFit && graphBoundsRef.current) {
        hasAutoFit = true;
        requestAnimationFrame(() => {
          if (svgSelectionRef.current && zoomBehaviorRef.current) {
            svgSelectionRef.current.call(zoomBehaviorRef.current.transform, buildFitTransform(graphBoundsRef.current, width, height));
          }
        });
      }
    });

    function dragstarted(event: any, d: any) {
      event.sourceEvent?.stopPropagation();
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [data, theme, graphWidth]);

  const zoomBy = (factor: number) => {
    if (!svgSelectionRef.current || !zoomBehaviorRef.current) return;
    svgSelectionRef.current.transition().duration(180).call(zoomBehaviorRef.current.scaleBy, factor);
  };

  const setZoomLevel = (nextZoom: number) => {
    if (!svgSelectionRef.current || !zoomBehaviorRef.current || !svgRef.current) return;
    svgSelectionRef.current.call(
      zoomBehaviorRef.current.scaleTo,
      Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, nextZoom)),
      [graphWidth / 2, GRAPH_HEIGHT / 2] as any,
    );
  };

  const fitToGraph = () => {
    if (!svgSelectionRef.current || !zoomBehaviorRef.current || !graphBoundsRef.current) return;
    svgSelectionRef.current
      .transition()
      .duration(220)
      .call(zoomBehaviorRef.current.transform, buildFitTransform(graphBoundsRef.current, graphWidth, GRAPH_HEIGHT));
  };

  const resetZoom = () => {
    if (!svgSelectionRef.current || !zoomBehaviorRef.current || !graphWidth) return;
    const resetTransform = d3.zoomIdentity.translate(graphWidth * 0.08, GRAPH_HEIGHT * 0.05).scale(DEFAULT_ZOOM);
    svgSelectionRef.current.transition().duration(220).call(zoomBehaviorRef.current.transform, resetTransform);
  };

  if (!data || !data.nodes?.length) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No knowledge graph data available
        </Typography>
      </Paper>
    );
  }

  const categories = Array.from(new Set(data.nodes.map((n: any) => n.category)));

  return (
    <Box>
      <Paper sx={{ p: 2.5, mb: 2, borderRadius: 5 }}>
        <Stack spacing={1.5}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }}>
            <Typography variant="h6">Concept graph</Typography>
            <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap">
              <Chip size="small" icon={<OpenWithRoundedIcon />} label={`Zoom ${zoomPercent}%`} variant="outlined" />
              <Box sx={{ width: 140, px: 0.5, display: { xs: 'none', sm: 'block' } }}>
                <Slider
                  size="small"
                  min={MIN_ZOOM * 100}
                  max={MAX_ZOOM * 100}
                  value={zoomPercent}
                  onChange={(_, value) => setZoomLevel(Number(value) / 100)}
                  aria-label="Graph zoom"
                />
              </Box>
              <Tooltip title="Zoom out">
                <IconButton size="small" onClick={() => zoomBy(0.82)} aria-label="Zoom out">
                  <RemoveRoundedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Zoom in">
                <IconButton size="small" onClick={() => zoomBy(1.18)} aria-label="Zoom in">
                  <AddRoundedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Reset view">
                <IconButton size="small" onClick={resetZoom} aria-label="Reset graph view">
                  <RestartAltRoundedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Fit graph to view">
                <IconButton size="small" onClick={fitToGraph} aria-label="Fit graph to view">
                  <FilterCenterFocusRoundedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
          {categories.map(cat => (
            <Chip
              key={cat}
              label={cat}
              size="small"
              sx={{
                bgcolor: cat === 'method' ? theme.palette.primary.main :
                         cat === 'dataset' ? theme.palette.secondary.main :
                         cat === 'metric' ? theme.palette.warning.main : '#8b5cf6',
                color: 'white'
              }}
            />
          ))}
          </Box>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2, overflow: 'hidden', borderRadius: 5 }}>
        <Box
          ref={containerRef}
          sx={{
            width: '100%',
            borderRadius: 4,
            overflow: 'hidden',
            background: (theme) => theme.palette.mode === 'dark'
              ? 'radial-gradient(circle at top, rgba(33,84,214,0.12), transparent 40%), rgba(255,255,255,0.01)'
              : 'radial-gradient(circle at top, rgba(33,84,214,0.08), transparent 42%), rgba(21,35,59,0.015)',
          }}
        >
          <svg ref={svgRef} style={{ width: '100%', height: GRAPH_HEIGHT, display: 'block' }} />
        </Box>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, textAlign: 'center' }}>
          Scroll or use the slider to zoom, drag the canvas to pan, drag nodes to rearrange them, and use fit view if the graph drifts out of frame.
        </Typography>
      </Paper>
    </Box>
  );
};

const buildFitTransform = (
  bounds: { minX: number; maxX: number; minY: number; maxY: number } | null,
  width: number,
  height: number,
) => {
  if (!bounds) {
    return d3.zoomIdentity.translate(width * 0.08, height * 0.05).scale(DEFAULT_ZOOM);
  }

  const padding = 72;
  const graphWidth = Math.max(bounds.maxX - bounds.minX, 1);
  const graphHeight = Math.max(bounds.maxY - bounds.minY, 1);
  const scale = Math.max(
    MIN_ZOOM,
    Math.min(
      MAX_ZOOM,
      Math.min((width - padding * 2) / graphWidth, (height - padding * 2) / graphHeight),
    ),
  );
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;

  return d3.zoomIdentity
    .translate(width / 2 - centerX * scale, height / 2 - centerY * scale)
    .scale(scale);
};
