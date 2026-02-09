// Network graph visualization with vis.js

let network = null;
let allNodes = [];
let allEdges = [];

// Fetch graph data and initialize
async function initGraph() {
    try {
        const response = await fetch('/api/graph');
        const data = await response.json();
        
        allNodes = data.nodes;
        allEdges = data.edges;
        
        renderGraph();
    } catch (error) {
        console.error('Error loading graph data:', error);
    }
}

function renderGraph() {
    const container = document.getElementById('graph-container');
    
    // Filter nodes and edges based on toggles
    const showMembers = document.getElementById('toggle-members').checked;
    const showAlliances = document.getElementById('toggle-alliances').checked;
    
    let filteredNodes = allNodes.filter(node => {
        if (node.type === 'member' && !showMembers) return false;
        if (node.type === 'alliance' && !showAlliances) return false;
        return true;
    });
    
    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));
    
    let filteredEdges = allEdges.filter(edge => {
        return visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to);
    });
    
    // Prepare data for vis.js
    const nodes = filteredNodes.map(node => ({
        id: node.id,
        label: node.label,
        size: node.size,
        color: {
            background: node.type === 'alliance' ? '#8b5cf6' : 
                       node.type === 'set' ? '#22c55e' : '#3b82f6',
            border: node.type === 'alliance' ? '#a78bfa' : 
                   node.type === 'set' ? '#4ade80' : '#60a5fa',
            highlight: {
                background: node.type === 'alliance' ? '#a78bfa' : 
                           node.type === 'set' ? '#4ade80' : '#60a5fa',
                border: '#fff'
            }
        },
        font: {
            color: '#ffffff',
            size: 14
        },
        borderWidth: 2
    }));
    
    const edges = filteredEdges.map(edge => ({
        from: edge.from,
        to: edge.to,
        color: edge.color.color,
        dashes: edge.dashes || false,
        width: 2
    }));
    
    const graphData = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    
    const options = {
        nodes: {
            shape: 'dot',
            scaling: {
                min: 10,
                max: 30
            }
        },
        edges: {
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            stabilization: {
                enabled: true,
                iterations: 100
            },
            barnesHut: {
                gravitationalConstant: -8000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04,
                damping: 0.09
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true
        }
    };
    
    // Create network
    network = new vis.Network(container, graphData, options);
    
    // Handle node clicks
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const [type, id] = nodeId.split('-');
            
            let url;
            if (type === 'member') url = `/members/${id}`;
            else if (type === 'set') url = `/sets/${id}`;
            else if (type === 'alliance') url = `/alliances/${id}`;
            
            if (url) {
                window.location.href = url;
            }
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    
    // Add event listeners for toggles
    document.getElementById('toggle-members').addEventListener('change', renderGraph);
    document.getElementById('toggle-alliances').addEventListener('change', renderGraph);
});
