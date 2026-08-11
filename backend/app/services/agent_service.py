"""
Agent Service Module
====================
Implements an intelligent IT service Agent that can autonomously call tools to solve user problems.

Design:
- Uses LangChain's Agent framework
- Implements three core tools: knowledge base query, ticket query, FAQ search
- Displays complete thinking process (Thought/Action/Observation)
- Learning focus: Understand how Agent works (Thought → Action → Observation → Loop until answer)

Agent Workflow (ReAct Pattern):
1. Thought: AI analyzes the user's question and decides what to do next
2. Action: Selects and calls the appropriate tool
3. Observation: Gets the result returned by the tool
4. Repeats until AI determines it can provide a final answer

Why Agent?
- Compared to normal chat, Agent can proactively call tools to get information
- Compared to normal RAG, Agent can decide whether to search, what to search, when to stop
- Can combine multiple tools to solve complex problems
"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.models import AgentStep, TicketInfo


class AgentService:
    """
    IT Service Agent Service Class
    
    Implements an intelligent Agent capable of calling multiple tools
    to help users resolve IT-related issues.
    """

    def __init__(self):
        """
        Initialize Agent service
        Creates tool list and Agent executor
        """
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()
        self.llm = self.llm_service.get_llm_instance(temperature=0.1)

        # Create tool list
        self.tools = self._create_tools()

        # Create Agent executor
        self.agent_executor = self._create_agent()

        # Mock ticket data (in production, should fetch from database or ticket system)
        self._mock_tickets = self._init_mock_tickets()

    def _init_mock_tickets(self) -> Dict[str, TicketInfo]:
        """
        Initialize mock ticket data
        Provides sample tickets for demonstrating ticket query functionality
        """
        tickets = [
            TicketInfo(
                ticket_id="IT-2024-001",
                title="Cannot connect to company VPN",
                status="Resolved",
                submitter="Zhang San",
                create_time="2024-01-15 09:30:00",
                assignee="Engineer Li",
                description="User reports unable to connect to company VPN while working from home, authentication failed."
            ),
            TicketInfo(
                ticket_id="IT-2024-002",
                title="Email password reset request",
                status="In Progress",
                submitter="Li Si",
                create_time="2024-01-16 14:20:00",
                assignee="Engineer Wang",
                description="User forgot email password, needs to reset."
            ),
            TicketInfo(
                ticket_id="IT-2024-003",
                title="Outlook cannot send/receive emails",
                status="Pending",
                submitter="Wang Wu",
                create_time="2024-01-17 10:15:00",
                assignee=None,
                description="User reports Outlook client cannot send/receive emails normally, error message is unclear."
            ),
            TicketInfo(
                ticket_id="IT-2024-004",
                title="Office software installation request",
                status="Closed",
                submitter="Zhao Liu",
                create_time="2024-01-10 16:00:00",
                assignee="Engineer Zhang",
                description="New employee needs Office software suite installed."
            ),
        ]
        return {t.ticket_id: t for t in tickets}

    def _create_tools(self) -> List[Tool]:
        """
        Create tool list available for Agent
        
        Each tool includes:
        - name: Tool name (Agent identifies tool by name)
        - func: Tool execution function
        - description: Tool description (Agent decides whether to use this tool based on description)
        
        Note: description is very important! Agent uses description to decide when to use which tool,
        so description should be clear, accurate, and explain the tool's purpose and applicable scenarios.
        """
        tools = [
            # Tool 1: Knowledge Base Query
            Tool(
                name="knowledge_base",
                func=self._tool_knowledge_base,
                description="""Use this tool to query the IT knowledge base for documentation and solutions.
Use when the user asks about technical questions, operation steps, or troubleshooting methods.
Input should be a specific problem description.""",
            ),
            # Tool 2: Ticket Query
            Tool(
                name="ticket_query",
                func=self._tool_ticket_query,
                description="""Use this tool to query IT ticket status and details.
Use when the user asks about ticket number, ticket status, or ticket processing progress.
Input should be a ticket number (e.g., IT-2024-001).
If the user does not provide a ticket number, ask for it first.""",
            ),
            # Tool 3: FAQ Search
            Tool(
                name="faq_search",
                func=self._tool_faq_search,
                description="""Use this tool to search for common questions (FAQ) and standard answers.
Use when the user asks common, repetitive IT questions.
Input should be question keywords or a short description.""",
            ),
        ]
        return tools

    def _tool_knowledge_base(self, query: str) -> str:
        """
        Tool: Knowledge Base Query
        
        Calls RAG service to query knowledge base and returns related content.
        Note: Returns text string to Agent, Agent will continue thinking based on content.
        """
        try:
            # Query knowledge base
            source_docs = self.rag_service.search(query, top_k=3)

            if not source_docs:
                return "No related content found in the knowledge base."

            # Format results
            result_parts = []
            for i, doc in enumerate(source_docs, 1):
                result_parts.append(
                    f"[Document {i}] Source: {doc.source}\nContent: {doc.content}"
                )

            return "\n\n".join(result_parts)
        except Exception as e:
            return f"Knowledge base query error: {str(e)}"

    def _tool_ticket_query(self, ticket_id: str) -> str:
        """
        Tool: Ticket Query
        
        Queries ticket details by ticket number (using mock data).
        In production, should call ticket system API.
        """
        # Clean input (remove spaces, etc.)
        ticket_id = ticket_id.strip()

        # Find ticket
        ticket = self._mock_tickets.get(ticket_id)

        if ticket:
            return f"""Ticket Information:
Ticket ID: {ticket.ticket_id}
Title: {ticket.title}
Status: {ticket.status}
Submitter: {ticket.submitter}
Created: {ticket.create_time}
Assignee: {ticket.assignee or 'Unassigned'}
Description: {ticket.description}"""
        else:
            # Try fuzzy match (if input is partial ticket ID)
            matched = [t for t in self._mock_tickets.values()
                       if ticket_id.lower() in t.ticket_id.lower()
                       or ticket_id.lower() in t.title.lower()]

            if matched:
                result = "Found the following matching tickets:\n\n"
                for t in matched[:3]:
                    result += f"- {t.ticket_id}: {t.title} ({t.status})\n"
                result += "\nPlease provide the full ticket ID for detailed information."
                return result
            else:
                return f"No ticket found with ID '{ticket_id}'. Please verify the ticket ID."

    def _tool_faq_search(self, keyword: str) -> str:
        """
        Tool: FAQ Search
        
        Simulates FAQ search functionality, returns common questions and answers.
        In production, should search from FAQ database or knowledge base.
        """
        # Mock FAQ database
        faq_data = [
            {
                "question": "How to reset email password?",
                "answer": """Email password reset steps:
1. Visit the company email login page
2. Click "Forgot Password" link
3. Enter your email address and employee ID
4. System will send a verification code to your phone
5. Enter the verification code and set a new password
6. Password requirements: 8+ characters, including uppercase, lowercase, and numbers

If you cannot reset via self-service, please contact the IT service desk."""
            },
            {
                "question": "How to connect to company VPN?",
                "answer": """VPN connection steps:
1. Ensure VPN client software is installed
2. Open VPN client, enter server address: vpn.company.com
3. Log in with domain account and password
4. First-time connection requires installing security certificate
5. After connection, you can access company internal resources

Note: VPN password is the same as domain account password, must be changed every 90 days."""
            },
            {
                "question": "Computer boots up slowly, what to do?",
                "answer": """Common solutions for slow boot:
1. Clean startup items: Task Manager → Startup → Disable unnecessary startup items
2. Clean disk garbage: Right-click C drive → Properties → Disk Cleanup
3. Check for viruses: Run full disk scan with antivirus software
4. Add memory: If RAM is less than 8GB, consider upgrading
5. Replace with SSD: Replacing mechanical hard drive with SSD can significantly improve speed

If above methods don't work, please submit an IT ticket."""
            },
            {
                "question": "How to configure corporate email on mobile phone?",
                "answer": """Mobile email configuration steps:
1. Open phone's mail app
2. Select "Exchange" or "Corporate Email" type
3. Enter full email address and password
4. Server address: mail.company.com
5. Domain: company
6. Security type: SSL/TLS
7. Click Next, wait for verification to complete

iPhone users refer to: Settings → Mail → Add Account → Exchange"""
            },
            {
                "question": "Cannot connect to WiFi, what to do?",
                "answer": """WiFi connection troubleshooting:
1. Confirm WiFi switch is turned on
2. Forget network and reconnect
3. Check if password is correct (case-sensitive)
4. Restart router and device
5. Confirm wireless router is working normally
6. Check for IP conflicts

Company WiFi name: Company-WiFi, please consult department admin for password."""
            },
            {
                "question": "What to do if phone is lost?",
                "answer": """Lost phone handling guide:
1. Visit the company IT main page
2. Click "Lost Phone" link
3. Enter your email address and employee ID
4. Register the specific time and location of loss
5. IT service desk will remotely lock your corporate account to prevent data leakage
            
If you have further questions, please contact the IT service desk."""
            },
        ]

        # Simple keyword matching
        keyword_lower = keyword.lower()
        matched_faqs = []

        for faq in faq_data:
            if (keyword_lower in faq["question"].lower() or
                    keyword_lower in faq["answer"].lower()):
                matched_faqs.append(faq)

        if matched_faqs:
            result = "Found the following common questions:\n\n"
            for i, faq in enumerate(matched_faqs, 1):
                result += f"[Q{i}] {faq['question']}\n[A] {faq['answer']}\n\n"
            return result
        else:
            return "No matching common questions found. Suggest using knowledge base query for more detailed information."

    def _create_agent(self) -> AgentExecutor:
        """
        Create Agent executor
        
        Uses ReAct (Reasoning + Acting) pattern Agent,
        with all-English Prompt and English tool names to avoid encoding and parsing issues.
        """
        template = """You are a professional enterprise IT service assistant. You have access to the following tools:

{tools}

Use the following format EXACTLY:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL RULES:
1. ALWAYS start with "Thought:" followed by either "Action:" or "Final Answer:"
2. When you have enough information, output "Thought: I now know the final answer" then "Final Answer: ..."
3. NEVER output content without using the proper format
4. The Action MUST be exactly one of: [{tool_names}]
5. ALL responses MUST be in English ONLY - never use Chinese or any other language
6. Keep your Final Answer concise and helpful
7. If you cannot find relevant information, clearly state that in English

Begin!

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            max_execution_time=60,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        return agent_executor

    def run_query(self, query: str, show_thinking: bool = True) -> tuple:
        """
        Run Agent query
        
        Args:
            query: User question
            show_thinking: Whether to return detailed thinking process
        
        Returns:
            (final_answer, steps, tools_used)
        """
        try:
            # Call Agent executor
            result = self.agent_executor.invoke({"input": query})

            # Extract final answer
            final_answer = result.get("output", "Sorry, I cannot answer this question.")

            # Extract intermediate steps (thinking process)
            steps = []
            tools_used = []

            if show_thinking:
                intermediate_steps = result.get("intermediate_steps", [])

                for i, step in enumerate(intermediate_steps):
                    action, observation = step

                    # Extract tool name
                    tool_name = action.tool if hasattr(action, 'tool') else str(action.tool)

                    # Extract tool input
                    tool_input = action.tool_input if hasattr(action, 'tool_input') else str(action)

                    # Thought step
                    steps.append(AgentStep(
                        step_type="thought",
                        content=f"Round {i+1}: I need to use the '{tool_name}' tool to gather more information."
                    ))

                    # Action step
                    steps.append(AgentStep(
                        step_type="action",
                        content=f"Calling tool: {tool_name}\nInput: {tool_input}",
                        tool=tool_name
                    ))

                    # Observation step
                    obs_content = observation
                    if isinstance(obs_content, Exception):
                        obs_content = f"Tool call error: {str(obs_content)}"
                    # Truncate if too long
                    if len(str(obs_content)) > 500:
                        obs_content = str(obs_content)[:500] + "\n... (content truncated)"
                    steps.append(AgentStep(
                        step_type="observation",
                        content=str(obs_content)
                    ))

                    # Record used tools
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)

            return final_answer, steps, tools_used

        except Exception as e:
            print(f"[Agent Error] {str(e)}")
            error_answer = f"An error occurred while processing your request: {str(e)}\n\nPlease try again or contact IT support."
            return error_answer, [], []

    def get_available_tools(self) -> List[dict]:
        """Get available tools list (for frontend display)"""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools
        ]

    def get_all_tickets(self) -> List[TicketInfo]:
        """Get all tickets (for admin interface display)"""
        return list(self._mock_tickets.values())


# Global singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """
    Get Agent service singleton
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service