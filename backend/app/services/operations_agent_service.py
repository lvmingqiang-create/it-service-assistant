"""
IT Operations Agent Service

Provides system operations capabilities:
- System status checking
- Service management (start/stop/restart)
- Log querying
- Resource monitoring

This Agent is designed for IT operations scenarios,
complementing the IT Service Agent (which handles user-facing Q&A).
"""

from typing import List, Optional
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class OperationsAgentService:
    """
    IT Operations Agent Service Class
    
    Implements an intelligent Agent capable of performing
    IT operations tasks such as system monitoring and service management.
    """

    def __init__(self):
        self.llm = self._create_llm()
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()

    def _create_llm(self) -> ChatOpenAI:
        """Create LLM instance with optimized settings for operations tasks."""
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=0.1,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

    def _create_tools(self) -> List[Tool]:
        """
        Create tool list available for Operations Agent
        
        Each tool includes:
        - name: Tool name (Agent identifies tool by name)
        - func: Tool execution function
        - description: Tool description (Agent decides whether to use this tool based on description)
        """
        tools = [
            # Tool 1: System Status Check
            Tool(
                name="system_status",
                func=self._tool_system_status,
                description="""Use this tool to check the overall status of IT systems and servers.
Use when the user asks about system health, server status, or whether systems are running normally.
Input should be a system name or 'all' to check all systems.""",
            ),
            # Tool 2: Service Management
            Tool(
                name="service_manage",
                func=self._tool_service_manage,
                description="""Use this tool to manage IT services (start, stop, restart, check status).
Use when the user needs to start, stop, or restart a service, or check service status.
Input should be in format: "action service_name" (e.g., "restart nginx", "status mysql").""",
            ),
            # Tool 3: Log Query
            Tool(
                name="log_query",
                func=self._tool_log_query,
                description="""Use this tool to query system and application logs.
Use when the user needs to check logs for troubleshooting or auditing.
Input should be a service name or log type (e.g., "nginx", "application", "security").""",
            ),
            # Tool 4: Resource Monitor
            Tool(
                name="resource_monitor",
                func=self._tool_resource_monitor,
                description="""Use this tool to check server resource usage (CPU, memory, disk).
Use when the user asks about resource utilization, performance issues, or capacity planning.
Input should be a resource type: "cpu", "memory", "disk", or "all".""",
            ),
        ]
        return tools

    def _tool_system_status(self, query: str) -> str:
        """
        Tool: System Status Check
        
        Returns the current status of IT systems.
        """
        systems = {
            "web_server": {"status": "running", "uptime": "15 days", "health": "healthy"},
            "database": {"status": "running", "uptime": "30 days", "health": "healthy"},
            "mail_server": {"status": "running", "uptime": "7 days", "health": "warning"},
            "file_server": {"status": "stopped", "uptime": "N/A", "health": "critical"},
        }

        if query.lower() == "all":
            result = "System Status Report:\n\n"
            for name, info in systems.items():
                result += f"- {name}: Status={info['status']}, Uptime={info['uptime']}, Health={info['health']}\n"
            return result

        system_name = query.lower().replace(" ", "_")
        if system_name in systems:
            info = systems[system_name]
            return f"System: {system_name}\nStatus: {info['status']}\nUptime: {info['uptime']}\nHealth: {info['health']}"
        
        return f"System '{query}' not found. Available systems: {', '.join(systems.keys())}"

    def _tool_service_manage(self, query: str) -> str:
        """
        Tool: Service Management
        
        Manages IT services (start, stop, restart, status).
        """
        parts = query.strip().split(maxsplit=1)
        if len(parts) < 2:
            return "Error: Please provide action and service name. Format: 'action service_name' (e.g., 'restart nginx')"

        action = parts[0].lower()
        service = parts[1].lower()

        valid_actions = ["start", "stop", "restart", "status"]
        if action not in valid_actions:
            return f"Error: Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}"

        services = {
            "nginx": {"status": "running", "pid": 1234},
            "mysql": {"status": "running", "pid": 5678},
            "redis": {"status": "running", "pid": 9012},
            "app_server": {"status": "stopped", "pid": None},
        }

        if service not in services:
            return f"Service '{service}' not found. Available services: {', '.join(services.keys())}"

        if action == "status":
            info = services[service]
            return f"Service: {service}\nStatus: {info['status']}\nPID: {info['pid'] or 'N/A'}"

        if action == "start" and services[service]["status"] == "running":
            return f"Service '{service}' is already running."

        if action == "stop" and services[service]["status"] == "stopped":
            return f"Service '{service}' is already stopped."

        if action == "restart":
            return f"Service '{service}' has been restarted successfully."

        if action == "start":
            return f"Service '{service}' has been started successfully."

        if action == "stop":
            return f"Service '{service}' has been stopped successfully."

        return f"Action '{action}' completed for service '{service}'."

    def _tool_log_query(self, query: str) -> str:
        """
        Tool: Log Query
        
        Queries system and application logs.
        """
        logs = {
            "nginx": [
                "2024-01-15 10:23:45 INFO: Request processed successfully",
                "2024-01-15 10:24:12 WARN: High response time detected (2.5s)",
                "2024-01-15 10:25:00 ERROR: Connection timeout to upstream server",
            ],
            "mysql": [
                "2024-01-15 10:20:00 INFO: Database backup completed",
                "2024-01-15 10:22:30 WARN: Slow query detected (3.2s)",
                "2024-01-15 10:23:00 INFO: Connection pool refreshed",
            ],
            "application": [
                "2024-01-15 10:21:00 INFO: User authentication successful",
                "2024-01-15 10:22:00 ERROR: Failed to process payment request",
                "2024-01-15 10:23:00 WARN: API rate limit approaching",
            ],
            "security": [
                "2024-01-15 10:19:00 INFO: Firewall rules updated",
                "2024-01-15 10:20:30 WARN: Failed login attempt from 192.168.1.100",
                "2024-01-15 10:21:00 INFO: SSL certificate renewed",
            ],
        }

        log_type = query.lower().strip()
        if log_type in logs:
            result = f"Logs for '{log_type}':\n\n"
            for entry in logs[log_type]:
                result += f"  {entry}\n"
            return result

        return f"Log type '{query}' not found. Available types: {', '.join(logs.keys())}"

    def _tool_resource_monitor(self, query: str) -> str:
        """
        Tool: Resource Monitor
        
        Checks server resource usage.
        """
        resources = {
            "cpu": {"usage": "45%", "cores": 8, "load_avg": "2.1, 1.8, 1.5"},
            "memory": {"total": "32GB", "used": "18GB", "available": "14GB", "usage_percent": "56%"},
            "disk": {"total": "500GB", "used": "320GB", "available": "180GB", "usage_percent": "64%"},
        }

        if query.lower() == "all":
            result = "Resource Usage Report:\n\n"
            for name, info in resources.items():
                if name == "cpu":
                    result += f"CPU: Usage={info['usage']}, Cores={info['cores']}, Load Avg={info['load_avg']}\n"
                else:
                    result += f"{name.upper()}: Total={info['total']}, Used={info['used']}, Available={info['available']}, Usage={info['usage_percent']}\n"
            return result

        resource_type = query.lower().strip()
        if resource_type in resources:
            info = resources[resource_type]
            if resource_type == "cpu":
                return f"CPU Usage: {info['usage']}\nCores: {info['cores']}\nLoad Average: {info['load_avg']}"
            else:
                return f"{resource_type.upper()} Usage:\nTotal: {info['total']}\nUsed: {info['used']}\nAvailable: {info['available']}\nUsage: {info['usage_percent']}"

        return f"Resource type '{query}' not found. Available types: {', '.join(resources.keys())}"

    def _create_agent(self) -> AgentExecutor:
        """
        Create Agent executor for Operations Agent
        
        Uses ReAct (Reasoning + Acting) pattern with all-English Prompt.
        """
        template = """You are a professional IT Operations Agent. You have access to the following tools:

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
6. STRICT: Your answer MUST be based ONLY on the Observation from tools. DO NOT use your own knowledge or training data to answer.
7. If the Observation does not contain relevant information, say EXACTLY: "I couldn't retrieve the requested information. Please check the system manually or contact the IT operations team."
8. NEVER fabricate system status, log entries, resource metrics, contact information, or procedures that are not explicitly stated in the tool Observation
9. For operations tasks, always confirm the action was completed successfully based on actual tool output
10. If the user asks a greeting or casual question, respond briefly and offer to help with IT operations tasks

Begin!

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def run_query(self, query: str, show_thinking: bool = True, history: Optional[List[dict]] = None) -> tuple:
        """
        Run Operations Agent query
        
        Args:
            query: User question or operation request
            show_thinking: Whether to return detailed thinking process
            history: Conversation history (last 10 messages)
        
        Returns:
            (final_answer, steps, tools_used)
        """
        try:
            input_text = query
            if history and len(history) > 0:
                history_context = "\n".join([
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                    for msg in history[-10:]
                ])
                input_text = f"Previous conversation:\n{history_context}\n\nCurrent question: {query}"

            result = self.agent_executor.invoke({"input": input_text})

            answer = result.get("output", "No response generated.")
            intermediate_steps = result.get("intermediate_steps", [])

            steps = []
            tools_used = []

            for step in intermediate_steps:
                tool_call, tool_output = step
                tool_name = tool_call.tool
                tool_input = tool_call.tool_input

                tools_used.append(tool_name)

                if show_thinking:
                    steps.append({
                        "type": "thought",
                        "content": f"Using tool: {tool_name}",
                    })
                    steps.append({
                        "type": "action",
                        "content": f"Calling tool: {tool_name} Input: {tool_input}",
                    })
                    steps.append({
                        "type": "observation",
                        "content": str(tool_output)[:500],
                    })

            return answer, steps, tools_used

        except Exception as e:
            error_msg = f"Operations Agent error: {str(e)}"
            print(f"[Operations Agent Error] {error_msg}")
            return error_msg, [], []