import { create } from 'zustand';
import type { GraphData, GraphNode, GraphLink } from '../types';

interface GraphStore {
  // 상태
  nodes: GraphNode[];
  links: GraphLink[];
  selectedNode: GraphNode | null;

  // 액션
  setGraphData: (data: GraphData) => void;
  addNode: (node: GraphNode) => void;
  addLink: (link: GraphLink) => void;
  selectNode: (node: GraphNode | null) => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
  nodes: [],
  links: [],
  selectedNode: null,

  setGraphData: (data) =>
    set({
      nodes: data.nodes,
      links: data.links,
    }),

  addNode: (node) =>
    set((state) => {
      // 중복 방지
      if (state.nodes.find((n) => n.id === node.id)) {
        return state;
      }
      return { nodes: [...state.nodes, node] };
    }),

  addLink: (link) =>
    set((state) => ({
      links: [...state.links, link],
    })),

  selectNode: (node) => set({ selectedNode: node }),

  clearGraph: () => set({ nodes: [], links: [], selectedNode: null }),
}));
