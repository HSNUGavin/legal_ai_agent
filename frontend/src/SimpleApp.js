// Get React and ReactDOM from the global scope (loaded via CDN)
const { useState, useEffect, useRef } = React;

// 渲染 Markdown 內容
const renderMarkdown = (text) => {
    // 使用 marked.js 解析 Markdown
    if (typeof marked !== 'undefined') {
        return <div dangerouslySetInnerHTML={{ __html: marked.parse(text) }} />;
    }
    // 如果 marked 不可用，則返回純文本
    return <div>{text}</div>;
};

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
                
                // 提取內容 - 只在完成時顯示最終內容
                const contentMatch = processedResponse.match(/<content>(.*?)<\/content>/s);
                const currentContent = contentMatch ? contentMatch[1] : processedResponse;
                
                // 更新消息，只在完成時顯示最終內容
                if (decision === 'finish') {
                    // 如果完成，添加最終消息
                    setMessages(prev => {
                        // 過濾掉之前可能添加的臨時 AI 消息和系統消息
                        const filteredPrev = prev.filter(msg => !(msg.sender === 'ai' && msg.temporary) && msg.sender !== 'system');
                        return [...filteredPrev, { text: currentContent, sender: 'ai' }];
                    });
                    setIsLoading(false);
                    break;
                } else {
                    // 檢查是否有動作需要執行
                    const actionMatch = processedResponse.match(/<action>(.*?)<\/action>/);
                    
                    if (actionMatch) {
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
        const actionMatch = response.match(/<action>(.*?)<\/action>/);
        
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
        
        // 如果有動作標籤，添加到思考步驟中
        if (actionMatch) {
            const actionContent = actionMatch[1];
            steps.push({ action: actionContent });
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
                <h2>透過 AI 搜尋資料庫內的台灣法律判決書</h2>
            </div>
            
            <button className="reset-button" onClick={handleReset}>
                重置對話
            </button>
            
            <div className="chat-container">
                <div className="messages-container">
                    <div className="messages">
                        {messages.map((message, index) => (
                            <div key={index} className={`message ${message.sender}-message`}>
                                {message.sender === 'user' ? (
                                    message.text
                                ) : (
                                    renderMarkdown(message.text)
                                )}
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
                                {step.action && (
                                    <div className="thinking-node action-node">
                                        <strong>動作:</strong> {step.action}
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
