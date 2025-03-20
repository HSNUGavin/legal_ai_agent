// Get React and ReactDOM from the global scope (loaded via CDN)
const { useState, useEffect, useRef } = React;
const ReactFlow = window.ReactFlow || window.reactFlowExports;
const { Background, Controls, MiniMap } = ReactFlow;

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [thinkingSteps, setThinkingSteps] = useState([]);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const messagesEndRef = useRef(null);

    // Scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Update nodes and edges when thinking steps change
    useEffect(() => {
        if (thinkingSteps.length > 0) {
            const newNodes = [];
            const newEdges = [];
            
            thinkingSteps.forEach((step, index) => {
                // Create nodes for each thinking step
                if (step.strategy) {
                    newNodes.push({
                        id: `strategy-${index}`,
                        data: { label: `策略: ${step.strategy}` },
                        position: { x: 100, y: 100 + index * 150 },
                        className: 'thinking-node strategy-node'
                    });
                }
                
                if (step.think) {
                    newNodes.push({
                        id: `think-${index}`,
                        data: { label: `思考: ${step.think}` },
                        position: { x: 350, y: 100 + index * 150 },
                        className: 'thinking-node think-node'
                    });
                }
                
                // Create edges between nodes
                if (index > 0) {
                    if (step.strategy && thinkingSteps[index-1].strategy) {
                        newEdges.push({
                            id: `edge-strategy-${index-1}-${index}`,
                            source: `strategy-${index-1}`,
                            target: `strategy-${index}`,
                            animated: true
                        });
                    }
                    
                    if (step.think && thinkingSteps[index-1].think) {
                        newEdges.push({
                            id: `edge-think-${index-1}-${index}`,
                            source: `think-${index-1}`,
                            target: `think-${index}`,
                            animated: true
                        });
                    }
                }
                
                // Connect strategy and think nodes
                if (step.strategy && step.think) {
                    newEdges.push({
                        id: `edge-strategy-think-${index}`,
                        source: `strategy-${index}`,
                        target: `think-${index}`,
                        animated: true
                    });
                }
            });
            
            setNodes(newNodes);
            setEdges(newEdges);
        }
    }, [thinkingSteps]);

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        
        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
        setIsLoading(true);
        setThinkingSteps([]);
        
        try {
            // Send POST request to streaming endpoint
            const response = await fetch('http://localhost:5000/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });
            
            // Create a new ReadableStream from the response body
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            // Process the stream
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'thinking') {
                                // Add thinking step
                                setThinkingSteps(prev => [...prev, data.data]);
                            } else if (data.type === 'final') {
                                // Add final response
                                setMessages(prev => [...prev, { text: data.data, sender: 'ai' }]);
                                setIsLoading(false);
                            }
                        } catch (error) {
                            console.error('Error parsing stream data:', error);
                        }
                    }
                }
            }
            
            setIsLoading(false);
        } catch (error) {
            console.error('Error:', error);
            setIsLoading(false);
            
            // Fallback to regular API
            handleFallbackSubmit(userMessage);
        }
    };
    
    // Fallback to regular API if streaming fails
    const handleFallbackSubmit = async (userMessage) => {
        try {
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });
            
            const data = await response.json();
            
            // Extract thinking steps
            const strategyMatches = data.response.match(/<strategy>(.*?)<\/strategy>/g) || [];
            const thinkMatches = data.response.match(/<think>(.*?)<\/think>/g) || [];
            
            const steps = [];
            const maxSteps = Math.max(strategyMatches.length, thinkMatches.length);
            
            for (let i = 0; i < maxSteps; i++) {
                const step = {};
                
                if (i < strategyMatches.length) {
                    const strategyContent = strategyMatches[i].replace(/<\/?strategy>/g, '');
                    step.strategy = strategyContent;
                }
                
                if (i < thinkMatches.length) {
                    const thinkContent = thinkMatches[i].replace(/<\/?think>/g, '');
                    step.think = thinkContent;
                }
                
                steps.push(step);
            }
            
            setThinkingSteps(steps);
            
            // Extract content
            const contentMatch = data.response.match(/<content>(.*?)<\/content>/s);
            const content = contentMatch ? contentMatch[1] : data.response;
            
            setMessages(prev => [...prev, { text: content, sender: 'ai' }]);
            setIsLoading(false);
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, { text: '抱歉，發生錯誤，請稍後再試。', sender: 'ai' }]);
            setIsLoading(false);
        }
    };

    // Reset conversation
    const handleReset = async () => {
        try {
            await fetch('http://localhost:5000/api/reset', {
                method: 'POST',
            });
            setMessages([]);
            setThinkingSteps([]);
            setNodes([]);
            setEdges([]);
        } catch (error) {
            console.error('Error resetting conversation:', error);
        }
    };

    return (
        <div className="app-container">
            <div className="header">
                <h1>法律 AI 助手</h1>
            </div>
            
            <button className="reset-button" onClick={handleReset}>
                重置對話
            </button>
            
            <div className="chat-container">
                <div className="messages-container">
                    <div className="messages">
                        {messages.map((message, index) => (
                            <div key={index} className={`message ${message.sender}-message`}>
                                {message.text}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="loading">
                                <div className="loading-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                    
                    <form className="input-container" onSubmit={handleSubmit}>
                        <textarea
                            className="message-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="請輸入您的問題..."
                            disabled={isLoading}
                            rows={3}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                        ></textarea>
                        <button className="send-button" type="submit" disabled={isLoading}>
                            發送
                        </button>
                    </form>
                </div>
                
                <div className="thinking-container">
                    <div className="thinking-header">AI 思考過程</div>
                    <div className="thinking-content">
                        <div className="thinking-flow">
                            <ReactFlow
                                nodes={nodes}
                                edges={edges}
                                fitView
                            >
                                <Background />
                                <Controls />
                            </ReactFlow>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
