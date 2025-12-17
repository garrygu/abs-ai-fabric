# Onyx Chat UI User Manual

## 🎯 Welcome to Onyx Chat

Onyx Chat provides a powerful conversational interface for interacting with AI models, managing documents, and executing specialized agents. This manual will guide you through all the features and capabilities.

---

## 🚀 Getting Started

### First Steps
1. **Access Onyx Chat**: Open http://localhost:8000 in your browser
2. **Start Chatting**: Type your first message in the input field
3. **Explore Features**: Use the sidebar to discover additional capabilities

### Interface Overview
```
┌─────────────────────────────────────────────────────────┐
│  Onyx AI Assistant                    [Settings] [Help] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  👤 You: Hello, can you help me analyze a contract?     │
│                                                         │
│  🤖 Onyx: I'd be happy to help you analyze a contract! │
│     I can review documents, identify risks, extract     │
│     key clauses, and provide recommendations.          │
│                                                         │
│  👤 You: [Type your message here...]              [📎] │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💬 Basic Chat Features

### Sending Messages
- **Type**: Enter your message in the text input field
- **Send**: Press Enter or click the Send button
- **Edit**: Click on your previous messages to edit them
- **Delete**: Right-click messages to delete them

### Message Types
- **Text Messages**: Standard conversational text
- **Code Blocks**: Use backticks for code formatting
- **File Attachments**: Upload documents for analysis
- **System Prompts**: Set context and instructions

### Chat History
- **Automatic Saving**: All conversations are saved automatically
- **Search History**: Use the search bar to find previous conversations
- **Export**: Download conversation history as JSON or text
- **Clear History**: Option to clear specific conversations

---

## 📁 Document Management

### Uploading Documents
1. **Click Attach**: Use the 📎 button or drag & drop files
2. **Supported Formats**: PDF, DOCX, TXT, MD, HTML
3. **Processing**: Documents are automatically chunked and indexed
4. **Status**: Watch the progress indicator during processing

### Document Features
- **Preview**: View document content before processing
- **Metadata**: Add custom metadata (source, date, type)
- **Collections**: Organize documents into collections
- **Search**: Find documents by content or metadata

### Document Library
Access your uploaded documents through the sidebar:
- **Recent**: Recently uploaded documents
- **Collections**: Organized by topic or project
- **Search**: Find documents by content
- **Manage**: Edit metadata, delete, or reprocess

---

## 🤖 Agent Management

### Available Agents
Onyx comes with several pre-configured agents:

#### Contract Review Agent
- **Purpose**: Analyze contracts for risks and key terms
- **Usage**: Upload contract → Select agent → Ask for analysis
- **Output**: Risk assessment, key clauses, recommendations

#### Document Q&A Agent
- **Purpose**: Answer questions about uploaded documents
- **Usage**: Upload document → Ask specific questions
- **Output**: Relevant excerpts with citations

#### Legal Research Agent
- **Purpose**: Research legal topics and precedents
- **Usage**: Ask legal questions → Get research results
- **Output**: Comprehensive research with sources

### Custom Agents
Create your own specialized agents:
1. **Agent Builder**: Use the agent creation interface
2. **Instructions**: Define the agent's behavior and capabilities
3. **Knowledge Base**: Connect to specific document collections
4. **Testing**: Test your agent before deployment

---

## 🔍 Advanced Features

### RAG (Retrieval-Augmented Generation)
- **Document Search**: Query your uploaded documents
- **Context-Aware**: Responses include relevant document excerpts
- **Citation Tracking**: See which documents informed the response
- **Relevance Scoring**: Understand how relevant each source is

### Web Search Integration
- **Current Information**: Access up-to-date information from the web
- **Source Verification**: See sources for web-sourced information
- **Fact Checking**: Cross-reference information across sources

### Code Execution
- **Python Support**: Execute Python code for calculations
- **Data Analysis**: Process and analyze data
- **Visualization**: Create charts and graphs
- **Safe Execution**: Code runs in a sandboxed environment

### Multi-Modal Capabilities
- **Text Analysis**: Process and analyze text content
- **Image Processing**: Analyze images and extract text
- **Document Parsing**: Extract structured data from documents
- **Format Conversion**: Convert between different document formats

---

## ⚙️ Settings & Configuration

### Chat Settings
Access settings through the gear icon (⚙️):

#### Model Selection
- **Available Models**: Choose from installed LLM models
- **Model Switching**: Change models mid-conversation
- **Performance**: Balance speed vs. quality

#### Response Parameters
- **Temperature**: Control creativity (0.0 = focused, 2.0 = creative)
- **Max Tokens**: Limit response length
- **Top P**: Control response diversity
- **Frequency Penalty**: Reduce repetition

#### Interface Preferences
- **Theme**: Light or dark mode
- **Font Size**: Adjustable text size
- **Language**: Interface language selection
- **Notifications**: Enable/disable notifications

### Agent Configuration
- **Default Agent**: Set your preferred agent
- **Agent Parameters**: Customize agent behavior
- **Knowledge Sources**: Connect agents to document collections
- **Response Format**: Define output structure

---

## 📊 Usage Analytics

### Conversation Metrics
- **Message Count**: Track conversation length
- **Token Usage**: Monitor API consumption
- **Response Time**: Measure response speed
- **Accuracy**: Rate response quality

### Document Analytics
- **Upload Statistics**: Track document processing
- **Search Queries**: Monitor document usage
- **Collection Growth**: Track knowledge base expansion
- **Processing Time**: Monitor document indexing speed

### Performance Insights
- **Model Performance**: Compare different models
- **Agent Effectiveness**: Track agent success rates
- **User Patterns**: Understand usage patterns
- **Optimization**: Identify improvement opportunities

---

## 🔧 Troubleshooting

### Common Issues

#### Chat Not Responding
**Symptoms**: Messages not being processed
**Solutions**:
1. Check internet connection
2. Refresh the page
3. Check service status at http://localhost:8000/health
4. Clear browser cache

#### Document Upload Failing
**Symptoms**: Documents not processing
**Solutions**:
1. Check file format (PDF, DOCX, TXT supported)
2. Ensure file size < 50MB
3. Try uploading in smaller chunks
4. Check document processing logs

#### Slow Responses
**Symptoms**: Long wait times for responses
**Solutions**:
1. Try a smaller model
2. Reduce max_tokens setting
3. Check system resources
4. Use caching for repeated queries

#### Agent Not Working
**Symptoms**: Agent responses are incorrect or missing
**Solutions**:
1. Check agent configuration
2. Verify knowledge base connection
3. Test with simpler queries
4. Review agent instructions

### Getting Help
- **In-App Help**: Click the help icon (❓) for contextual help
- **Documentation**: Access full documentation
- **Support**: Contact support for technical issues
- **Community**: Join the user community for tips and tricks

---

## 🎯 Best Practices

### Effective Chat Usage
1. **Be Specific**: Provide clear, specific questions
2. **Provide Context**: Include relevant background information
3. **Use Examples**: Give examples of desired output
4. **Iterate**: Refine questions based on responses

### Document Management
1. **Organize Collections**: Group related documents
2. **Add Metadata**: Include source, date, and type information
3. **Regular Updates**: Keep document collections current
4. **Quality Control**: Review processed documents for accuracy

### Agent Optimization
1. **Clear Instructions**: Define agent behavior clearly
2. **Relevant Knowledge**: Connect agents to appropriate documents
3. **Test Thoroughly**: Validate agent responses before deployment
4. **Monitor Performance**: Track agent effectiveness over time

### Performance Tips
1. **Model Selection**: Choose appropriate models for tasks
2. **Caching**: Use cached responses for repeated queries
3. **Batch Operations**: Process multiple documents together
4. **Resource Monitoring**: Keep an eye on system resources

---

## 📚 Advanced Workflows

### Contract Analysis Workflow
1. **Upload Contract**: Drag & drop contract PDF
2. **Select Agent**: Choose Contract Review Agent
3. **Initial Analysis**: Ask for high-level overview
4. **Deep Dive**: Request specific clause analysis
5. **Risk Assessment**: Get risk evaluation
6. **Export Report**: Download analysis results

### Research Workflow
1. **Define Topic**: Specify research question
2. **Web Search**: Enable web search for current information
3. **Document Review**: Search uploaded documents
4. **Synthesis**: Combine information from multiple sources
5. **Citation**: Track and cite all sources
6. **Summary**: Generate comprehensive summary

### Data Analysis Workflow
1. **Upload Data**: Provide data files or paste data
2. **Code Execution**: Use Python for analysis
3. **Visualization**: Create charts and graphs
4. **Interpretation**: Get AI interpretation of results
5. **Export**: Download analysis and visualizations

---

## 🔒 Security & Privacy

### Data Protection
- **Local Processing**: All processing happens on your local system
- **No External Sharing**: Documents stay within your environment
- **Encrypted Storage**: Data encrypted at rest
- **Access Control**: User-based access management

### Privacy Settings
- **Data Retention**: Control how long data is kept
- **Sharing Controls**: Manage what can be shared
- **Audit Logs**: Track data access and usage
- **Compliance**: Meet regulatory requirements

---

## 📞 Support & Resources

### Getting Help
- **In-App Support**: Use the help system within the chat
- **Documentation**: Access comprehensive guides
- **Video Tutorials**: Watch step-by-step guides
- **Community Forum**: Connect with other users

### Resources
- **API Documentation**: Technical integration guides
- **Best Practices**: Proven usage patterns
- **Templates**: Pre-built agent configurations
- **Examples**: Sample workflows and use cases

---

*This user manual is your complete guide to mastering Onyx Chat. For technical integration details, refer to the Onyx Integration Guide.*
