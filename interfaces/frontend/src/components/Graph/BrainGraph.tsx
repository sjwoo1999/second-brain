import { useCallback, useRef, useEffect, useState } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { useGraphStore } from '../../stores/graphStore';
import { useUIStore } from '../../stores/uiStore';
import type { GraphNode } from '../../types';
import * as THREE from 'three';

export function BrainGraph() {
  const { nodes, links, selectNode, selectedNode } = useGraphStore();
  const { showLegend, toggleLegend } = useUIStore();
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // 컨테이너 크기 감지
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // 노드 클릭 핸들러
  const handleNodeClick = useCallback(
    (node: any) => {
      selectNode(node as GraphNode);

      // 카메라 이동
      if (fgRef.current) {
        const distance = 100;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

        fgRef.current.cameraPosition(
          {
            x: node.x * distRatio,
            y: node.y * distRatio,
            z: node.z * distRatio,
          },
          node,
          1000
        );
      }
    },
    [selectNode]
  );

  // 노드 렌더링 커스터마이즈
  const nodeThreeObject = useCallback((node: any) => {
    const sphereGeometry = new THREE.SphereGeometry(5);
    const material = new THREE.MeshLambertMaterial({
      color: node.color || '#6366f1',
      transparent: true,
      opacity: 0.9,
    });
    const sphere = new THREE.Mesh(sphereGeometry, material);

    // 글로우 효과
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: node.color || '#6366f1',
      transparent: true,
      opacity: 0.3,
    });
    const glowSphere = new THREE.Mesh(
      new THREE.SphereGeometry(7),
      glowMaterial
    );
    sphere.add(glowSphere);

    return sphere;
  }, []);

  // 그래프 데이터 준비
  const graphData = {
    nodes: nodes.map((n) => ({ ...n })),
    links: links.map((l) => ({ ...l })),
  };

  // 노드 추가시 애니메이션
  useEffect(() => {
    if (fgRef.current && nodes.length > 0) {
      fgRef.current.d3Force('charge')?.strength(-100);
    }
  }, [nodes.length]);

  return (
    <div ref={containerRef} className="relative w-full h-full bg-[#0f0f23]">
      {dimensions.width > 0 && (
        <ForceGraph3D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel={(node: any) => `${node.label}`}
          nodeColor={(node: any) => node.color || '#6366f1'}
          nodeThreeObject={nodeThreeObject}
          linkColor={() => '#4a5568'}
          linkWidth={1}
          linkOpacity={0.4}
          backgroundColor="#0f0f23"
          onNodeClick={handleNodeClick}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
        />
      )}

      {/* 선택된 노드 정보 */}
      {selectedNode && (
        <div className="absolute bottom-4 left-2 right-2 sm:left-4 sm:right-4 bg-zinc-900/95 backdrop-blur-lg rounded-xl p-3 sm:p-4 border border-zinc-700/50 shadow-xl">
          <div className="flex items-start gap-3">
            <div
              className="w-3 h-3 sm:w-4 sm:h-4 rounded-full mt-1 shrink-0 ring-2 ring-white/20"
              style={{ backgroundColor: selectedNode.color }}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] sm:text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  {selectedNode.type}
                </span>
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-zinc-100 truncate">
                {selectedNode.label}
              </h3>
              {selectedNode.content && (
                <p className="text-xs sm:text-sm text-zinc-400 mt-1 line-clamp-2">
                  {selectedNode.content}
                </p>
              )}
            </div>
            <button
              onClick={() => selectNode(null)}
              className="text-zinc-500 hover:text-zinc-100 transition-colors p-1 hover:bg-zinc-800 rounded-lg"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 노드 통계 - 항상 표시 */}
      <div className="absolute top-3 left-3 sm:top-4 sm:left-4 bg-zinc-900/80 backdrop-blur-lg rounded-lg px-3 py-2 text-xs text-zinc-400 border border-zinc-800/50">
        <span className="text-violet-400 font-semibold">{nodes.length}</span> 노드
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-violet-400 font-semibold">{links.length}</span> 연결
      </div>

      {/* 범례 토글 버튼 */}
      <button
        onClick={toggleLegend}
        className="absolute top-3 right-3 sm:top-4 sm:right-4 bg-zinc-900/80 backdrop-blur-lg rounded-lg p-2 text-zinc-400 hover:text-zinc-100 transition-colors border border-zinc-800/50"
        title={showLegend ? '범례 숨기기' : '범례 보기'}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      {/* 범례 - 토글 가능 */}
      {showLegend && (
        <div className="absolute top-12 right-3 sm:top-14 sm:right-4 bg-zinc-900/90 backdrop-blur-lg rounded-lg p-3 border border-zinc-800/50 shadow-lg animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="text-[10px] sm:text-xs space-y-1.5">
            {[
              { color: 'bg-violet-500', label: 'Topic' },
              { color: 'bg-emerald-500', label: 'Tool' },
              { color: 'bg-amber-500', label: 'Knowledge' },
              { color: 'bg-blue-500', label: 'Question' },
              { color: 'bg-pink-500', label: 'Insight' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full ${item.color}`} />
                <span className="text-zinc-400">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 빈 상태 */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-zinc-600">
            <div className="text-5xl sm:text-6xl mb-4 opacity-50">🧠</div>
            <p className="text-sm sm:text-base">대화를 시작하면</p>
            <p className="text-sm sm:text-base">지식 그래프가 생성됩니다</p>
          </div>
        </div>
      )}
    </div>
  );
}
