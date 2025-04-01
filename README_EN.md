# Legal AI Assistant

A legal AI assistant system based on Python backend and React frontend, designed for analyzing legal cases and providing legal advice. This is the English documentation for a system primarily designed for Taiwan users.

> [中文版本](./README.md)

## Features

- Legal analysis using OpenAI GPT-4o model
- Interactive web interface displaying AI thinking process
- Support for SQL queries and file reading
- Real-time visualization of AI thinking steps
- Conversation history and reset functionality
- Support for Markdown formatted text display
- Optimized user interface with clear separation of thinking process and final response
- Multi-agent collaborative workflow for improved analysis quality

## System Architecture

- **Backend**: Flask API + OpenAI
- **Frontend**: React + ReactFlow + Marked.js
- **Database**: SQLite (automatically imported from CSV files)
- **Agent System**: Multi-stage agent workflow (Planning, Control, Analysis, Summary)

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
http://localhost:5000
```

## How to Use

1. Enter your legal question in the input box
2. The AI will display its thinking process in the right panel
3. The final response will be shown in the conversation box, supporting Markdown format
4. Click the "Reset Conversation" button to start a new conversation

## System Flow

1. User inputs a question
2. Planning agent analyzes the problem and formulates a strategy
3. Control agent coordinates task execution
4. Analysis/Search agents perform specific tasks (such as SQL queries or file reading)
5. Summary agent generates the final response and displays it to the user

## Technical Details

- Special tags (`<think>`, `<action>`, `<content>`, `<if_finish>`) are used to process AI responses
- The right panel displays thinking steps and executed actions
- The conversation area only shows the final cleaned content
- Supports Markdown formatting, including code blocks, tables, lists, etc.
