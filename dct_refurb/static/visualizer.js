// visualizer.js

let workflowNodes = []; // Stores information about nodes in the workflow area
let connections = []; // Stores information about connections between nodes
let selectedNode = null; // For connecting nodes

document.addEventListener('DOMContentLoaded', function() {
    const serviceMapDiv = document.getElementById('service-map');
    const workflowArea = document.getElementById('workflow-area');
    const generateStringBtn = document.getElementById('generate-string');
    const serviceStringOutput = document.getElementById('service-string-output');

    // Fetch services and make them draggable
    fetch('/api/services')
        .then(response => response.json())
        .then(response => {
            const services = response.peers;
            serviceMapDiv.innerHTML = '<h2>Available Services:</h2>';
            if (services && Object.keys(services).length > 0) {
                const ul = document.createElement('ul');
                // Iterate over the values of the services object
                Object.values(services).forEach(service => {
                    const li = document.createElement('li');
                    li.textContent = `Name: ${service.name}, Type: ${service.service_type}, Input: ${service.input_type || 'N/A'}, Output: ${service.output_type || 'N/A'}`;
                    li.dataset.serviceName = service.name;
                    li.dataset.serviceType = service.service_type;
                    li.dataset.inputType = service.input_type;
                    li.dataset.outputType = service.output_type;
                    li.draggable = true;
                    li.classList.add('draggable-service');
                    li.addEventListener('dragstart', handleDragStart);
                    ul.appendChild(li);
                });
                serviceMapDiv.appendChild(ul);
            } else {
                serviceMapDiv.innerHTML += '<p>No services found.</p>';
            }
        })
        .catch(error => {
            console.error('Error fetching services:', error);
            serviceMapDiv.innerHTML = '<p>Error loading services.</p>';
        });

    // Workflow Area Drag and Drop Handlers
    workflowArea.addEventListener('dragover', handleDragOver);
    workflowArea.addEventListener('drop', handleDrop);

    // Drag Start Handler
    function handleDragStart(e) {
        e.dataTransfer.setData('text/plain', JSON.stringify({
            name: e.target.dataset.serviceName,
            type: e.target.dataset.serviceType,
            inputType: e.target.dataset.inputType,
            outputType: e.target.dataset.outputType
        }));
        e.dataTransfer.effectAllowed = 'copy';
    }

    // Drag Over Handler
    function handleDragOver(e) {
        e.preventDefault(); // Necessary to allow dropping
        e.dataTransfer.dropEffect = 'copy';
    }

    // Drop Handler
    function handleDrop(e) {
        e.preventDefault();
        const data = JSON.parse(e.dataTransfer.getData('text/plain'));
        createWorkflowNode(data, e.clientX, e.clientY);
    }

    // Create Workflow Node
    function createWorkflowNode(serviceData, x, y) {
        const node = document.createElement('div');
        node.classList.add('workflow-node');
        node.textContent = serviceData.name;
        node.dataset.nodeId = Date.now(); // Unique ID for the node
        node.dataset.serviceName = serviceData.name;
        node.dataset.serviceType = serviceData.type;
        node.dataset.inputType = serviceData.inputType;
        node.dataset.outputType = serviceData.outputType;

        // Position the node relative to the workflow area
        const workflowAreaRect = workflowArea.getBoundingClientRect();
        node.style.left = `${x - workflowAreaRect.left}px`;
        node.style.top = `${y - workflowAreaRect.top}px`;

        workflowArea.appendChild(node);
        workflowNodes.push({
            id: node.dataset.nodeId,
            name: serviceData.name,
            type: serviceData.type,
            inputType: serviceData.inputType,
            outputType: serviceData.outputType,
            element: node,
            inputs: [], // To store incoming connections
            outputs: [] // To store outgoing connections
        });

        // Make the node draggable within the workflow area
        node.addEventListener('mousedown', handleNodeMouseDown);
        node.addEventListener('click', handleNodeClick);
    }

    // Handle Node Dragging (within workflow area)
    let activeNode = null;
    let offsetX, offsetY;

    function handleNodeMouseDown(e) {
        activeNode = e.target;
        offsetX = e.clientX - activeNode.getBoundingClientRect().left;
        offsetY = e.clientY - activeNode.getBoundingClientRect().top;
        workflowArea.addEventListener('mousemove', handleNodeMouseMove);
        workflowArea.addEventListener('mouseup', handleNodeMouseUp);
    }

    function handleNodeMouseMove(e) {
        if (!activeNode) return;
        const workflowAreaRect = workflowArea.getBoundingClientRect();
        activeNode.style.left = `${e.clientX - workflowAreaRect.left - offsetX}px`;
        activeNode.style.top = `${e.clientY - workflowAreaRect.top - offsetY}px`;
        updateConnections(); // Update lines when node moves
    }

    function handleNodeMouseUp() {
        activeNode = null;
        workflowArea.removeEventListener('mousemove', handleNodeMouseMove);
        workflowArea.removeEventListener('mouseup', handleNodeMouseUp);
    }

    // Handle Node Click for Connections
    function handleNodeClick(e) {
        const clickedNode = workflowNodes.find(node => node.element === e.target);
        if (!clickedNode) return;

        if (!selectedNode) {
            // First click: select this node as the source
            selectedNode = clickedNode;
            clickedNode.element.style.border = '2px solid blue'; // Highlight selected
        } else if (selectedNode === clickedNode) {
            // Clicking the same node again: deselect
            selectedNode.element.style.border = '1px solid #a0d0a0'; // Reset border
            selectedNode = null;
        } else {
            // Second click: attempt to connect selectedNode to clickedNode
            attemptConnection(selectedNode, clickedNode);
            selectedNode.element.style.border = '1px solid #a0d0a0'; // Reset border
            selectedNode = null;
        }
    }

    // Attempt to connect two nodes
    function attemptConnection(sourceNode, targetNode) {
        // Prevent self-connection
        if (sourceNode.id === targetNode.id) {
            console.warn('Cannot connect a node to itself.');
            return;
        }

        // Check for existing connection
        if (connections.some(conn => conn.source === sourceNode.id && conn.target === targetNode.id)) {
            console.warn('Connection already exists.');
            return;
        }

        // Validate compatibility
        if (sourceNode.outputType === 'N/A' || targetNode.inputType === 'N/A' || sourceNode.outputType !== targetNode.inputType) {
            alert(`Incompatible types: ${sourceNode.outputType} -> ${targetNode.inputType}`);
            console.error(`Incompatible types: ${sourceNode.outputType} -> ${targetNode.inputType}`);
            return;
        }

        // Create connection
        connections.push({
            source: sourceNode.id,
            target: targetNode.id,
            element: drawConnection(sourceNode.element, targetNode.element)
        });
        sourceNode.outputs.push(targetNode.id);
        targetNode.inputs.push(sourceNode.id);
        console.log(`Connected ${sourceNode.name} to ${targetNode.name}`);
    }

    // Draw a line between two elements
    function drawConnection(sourceElem, targetElem) {
        const line = document.createElement('div');
        line.classList.add('connection-line');
        workflowArea.appendChild(line);
        updateLinePosition(line, sourceElem, targetElem);
        return line;
    }

    // Update line position
    function updateLinePosition(line, sourceElem, targetElem) {
        const sourceRect = sourceElem.getBoundingClientRect();
        const targetRect = targetElem.getBoundingClientRect();
        const workflowRect = workflowArea.getBoundingClientRect();

        const x1 = sourceRect.left + sourceRect.width / 2 - workflowRect.left;
        const y1 = sourceRect.top + sourceRect.height / 2 - workflowRect.top;
        const x2 = targetRect.left + targetRect.width / 2 - workflowRect.left;
        const y2 = targetRect.top + targetRect.height / 2 - workflowRect.top;

        const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
        const length = Math.sqrt((x2 - x1)**2 + (y2 - y1)**2);

        line.style.width = `${length}px`;
        line.style.left = `${x1}px`;
        line.style.top = `${y1}px`;
        line.style.transformOrigin = '0 0';
        line.style.transform = `rotate(${angle}deg)`;
    }

    // Update all connection lines
    function updateConnections() {
        connections.forEach(conn => {
            const sourceNode = workflowNodes.find(node => node.id === conn.source);
            const targetNode = workflowNodes.find(node => node.id === conn.target);
            if (sourceNode && targetNode) {
                updateLinePosition(conn.element, sourceNode.element, targetNode.element);
            }
        });
    }

    // Generate Service String
    generateStringBtn.addEventListener('click', function() {
        const serviceString = generateServiceString();
        serviceStringOutput.textContent = JSON.stringify(serviceString, null, 2);
    });

    function generateServiceString() {
        // This is a simplified topological sort and string generation.
        // A more robust solution would handle cycles, multiple inputs/outputs, etc.

        const graph = new Map();
        const inDegree = new Map();

        workflowNodes.forEach(node => {
            graph.set(node.id, []);
            inDegree.set(node.id, 0);
        });

        connections.forEach(conn => {
            graph.get(conn.source).push(conn.target);
            inDegree.set(conn.target, inDegree.get(conn.target) + 1);
        });

        const queue = [];
        workflowNodes.forEach(node => {
            if (inDegree.get(node.id) === 0) {
                queue.push(node.id);
            }
        });

        const result = [];
        while (queue.length > 0) {
            const nodeId = queue.shift();
            const node = workflowNodes.find(n => n.id === nodeId);
            result.push({
                id: node.id,
                name: node.name,
                type: node.type,
                inputType: node.inputType,
                outputType: node.outputType
            });

            graph.get(nodeId).forEach(neighborId => {
                inDegree.set(neighborId, inDegree.get(neighborId) - 1);
                if (inDegree.get(neighborId) === 0) {
                    queue.push(neighborId);
                }
            });
        }

        if (result.length !== workflowNodes.length) {
            console.warn('Cycle detected or disconnected graph. Service string might be incomplete.');
            // For now, return what we have, but a real implementation would handle this more robustly.
        }

        return result;
    }
});
