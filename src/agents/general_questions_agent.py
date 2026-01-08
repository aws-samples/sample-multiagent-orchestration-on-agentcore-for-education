"""General Questions Agent - handles general educational system queries.

This agent is exposed as a tool that can be invoked by the orchestrator.
It handles general queries about school policies, procedures, and educational topics.
"""

from strands import Agent, tool

@tool
def answer_general_questions(query: str, persona: str = "student") -> str:
    """Tool that handles general educational system questions.
    
    Args:
        query: The general question about the educational system
        persona: The persona type making the request (default: "student")
    
    Returns:
        String response from the general questions agent
    """
    # Create the general questions agent
    general_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        system_prompt="""You are a General Questions Assistant for the educational system.

You can provide information about:
- School policies and procedures (enrollment, attendance, grading policies)
- General educational topics (curriculum, teaching methods, learning resources)
- System navigation and usage (how to use the platform, where to find information)
- Common questions about the educational platform (features, capabilities, support)

IMPORTANT ROUTING GUIDELINES:
When a question requires specialized knowledge or personal data, indicate routing:

1. For STUDENT-SPECIFIC queries (grades, tasks, courses):
   → Route to Educational Assistant

2. For TEACHER-SPECIFIC queries (course metrics, student performance):
   → Route to Teacher Assistant

3. For PAYMENT-SPECIFIC queries (tuition, receipts, payment status):
   → Route to Financial Assistant

4. For ADMINISTRATOR-SPECIFIC queries (operational reports):
   → Route to Virtual Secretary

For GENERAL questions, provide helpful, accurate information in a friendly manner.

Format your responses clearly and professionally.
"""
    )
    
    # Simple context with system information
    context = f"""Educational System Information:
[Requesting Persona: {persona}]

GRADING SYSTEM:
- Grades are on a 0-10 scale
- 5.0 is the passing grade
- Grades below 5.0 require additional support

PAYMENT SYSTEM:
- Monthly tuition is $600.00 per month
- Payments are due on the 1st of each month

COURSE SYSTEM:
- Students can enroll in multiple courses
- Each course has assigned teachers
- Tasks and assignments have due dates

SUPPORT SYSTEM:
- Educational Assistant: Helps students with academic queries
- Teacher Assistant: Helps teachers manage courses
- Financial Assistant: Helps with payment queries
- Virtual Secretary: Provides administrative reports
- General Questions: Answers general system questions (that's me!)

User Query: {query}
"""
    
    # Get response from the agent
    response = general_agent(context)
    
    return str(response)
