// Get React and ReactDOM from the global scope (loaded via CDN)
const { useState, useEffect, useRef } = React;

function SimpleApp() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [thinkingSteps, setThinkingSteps] = useState([]);
    const messagesEndRef = useRef(null);

    // Scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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
            let currentResponse = await fetchChatResponse(userMessage);
            let processedResponse = currentResponse;
            
            // 處理可能的多輪對話
            while (true) {
                // 檢查是否需要繼續處理
                const ifFinishMatch = processedResponse.match(/<if_finish>(.*?)<\/if_finish>/);
                const decision = ifFinishMatch ? ifFinishMatch[1].trim().toLowerCase() : 'finish';
                
                // 提取思考步驟
                extractThinkingSteps(processedResponse);
                
                // 提取內容 - 無論是否完成都顯示當前內容
                const contentMatch = processedResponse.match(/<content>(.*?)<\/content>/s);
                const currentContent = contentMatch ? contentMatch[1] : processedResponse;
                
                // 更新消息，顯示當前的思考內容
                if (decision === 'finish') {
                    // 如果完成，添加最終消息
                    setMessages(prev => {
                        // 過濾掉之前可能添加的臨時 AI 消息
                        const filteredPrev = prev.filter(msg => !(msg.sender === 'ai' && msg.temporary));
                        return [...filteredPrev, { text: currentContent, sender: 'ai' }];
                    });
                    setIsLoading(false);
                    break;
                } else {
                    // 如果未完成，添加臨時消息
                    setMessages(prev => {
                        // 過濾掉之前可能添加的臨時 AI 消息
                        const filteredPrev = prev.filter(msg => !(msg.sender === 'ai' && msg.temporary));
                        return [...filteredPrev, { 
                            text: currentContent || "思考中...", 
                            sender: 'ai', 
                            temporary: true 
                        }];
                    });
                    
                    // 檢查是否有動作需要執行
                    const actionMatch = processedResponse.match(/<action>(.*?)<\/action>/);
                    
                    if (actionMatch) {
                        // 顯示中間步驟
                        setMessages(prev => [...prev, { 
                            text: `執行動作: ${actionMatch[1]}`, 
                            sender: 'system' 
                        }]);
                        
                        // 繼續處理
                        const response = await fetch('http://localhost:5000/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ 
                                message: processedResponse,
                                isProcessing: true
                            }),
                        });
                        
                        const data = await response.json();
                        processedResponse = data.response;
                    } else {
                        // 沒有動作但需要繼續
                        const response = await fetch('http://localhost:5000/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ 
                                message: `[ORIGINAL_QUESTION] ${userMessage}`,
                                isProcessing: true
                            }),
                        });
                        
                        const data = await response.json();
                        processedResponse = data.response;
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, { text: '抱歉，發生錯誤，請稍後再試。', sender: 'ai' }]);
            setIsLoading(false);
        }
    };
    
    // 提取思考步驟
    const extractThinkingSteps = (response) => {
        // 提取思考步驟
        const strategyMatches = response.match(/<strategy>(.*?)<\/strategy>/g) || [];
        const thinkMatches = response.match(/<think>(.*?)<\/think>/g) || [];
        
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
            
            if (Object.keys(step).length > 0) {
                steps.push(step);
            }
        }
        
        setThinkingSteps(prev => [...prev, ...steps]);
    };
    
    // 獲取聊天回應
    const fetchChatResponse = async (message) => {
        const response = await fetch('http://localhost:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        const data = await response.json();
        return data.response;
    };

    // Reset conversation
    const handleReset = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                setMessages([]);
                setThinkingSteps([]);
                setInput('');
                console.log('對話已重置');
            } else {
                console.error('重置對話失敗:', data.message);
            }
        } catch (error) {
            console.error('重置對話時出錯:', error);
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
                        {thinkingSteps.map((step, index) => (
                            <div key={index} className="thinking-step">
                                {step.strategy && (
                                    <div className="thinking-node strategy-node">
                                        <strong>策略:</strong> {step.strategy}
                                    </div>
                                )}
                                {step.think && (
                                    <div className="thinking-node think-node">
                                        <strong>思考:</strong> {step.think}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<SimpleApp />);
