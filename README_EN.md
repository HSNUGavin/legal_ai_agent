# Legal AI Assistant

A legal AI assistant system based on Python backend and React frontend, designed for analyzing legal cases and providing legal advice. This is the English documentation for a system primarily designed for Taiwan users.

> [中文版本](./README.md)

## Features

- Legal analysis using OpenAI GPT-4o model
- Interactive web interface displaying AI thinking process
- Support for SQL queries and file reading
- Real-time visualization of AI thinking steps
- Conversation history and reset functionality

## System Architecture

- **Backend**: Flask API + OpenAI
- **Frontend**: React + ReactFlow
- **Database**: SQLite (automatically imported from CSV files)

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

Create a `.env` file and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Flask API server:

```bash
python api.py
```

2. Open the frontend page in your browser:

```
frontend/index.html
```

## How to Use

1. Enter your legal question in the input box
2. The AI will display its thinking process in the right panel
3. The final response will be shown in the conversation box
4. Click the "Reset Conversation" button to start a new conversation

## System Flow

1. User inputs a question
2. AI analyzes the question and displays its thinking process
3. AI may execute SQL queries or read files
4. Final response is generated and displayed to the user
