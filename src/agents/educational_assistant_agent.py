"""Educational Assistant Agent - handles student academic queries.

This agent is exposed as a tool that can be invoked by the orchestrator.
It returns dummy data for demonstration purposes.
"""

import os
import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)

def load_env_variables():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent.parent / '.env'
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        logger.info(f"Loaded environment variables from {env_file}")
    else:
        logger.warning(f"Environment file not found at {env_file}")

def get_kb_id_from_ssm():
    param_name = '/app/octank_assistant/agentcore/kb_id'
    ssm = boto3.client("ssm")
    try:
        response = ssm.get_parameter(Name=param_name)
        kb_id = response["Parameter"]["Value"]
        logger.info(f"Octank Assistant runtime - get_kb_id_from_ssm kb_id: {kb_id}")
        return kb_id
    except ClientError as e:
        raise Exception(f"Could not retrieve kb_id from SSM: {e}")
        
#############
# IMPORTANT: Load .env variables and set environment variables BEFORE importing strands_tools
load_env_variables()

# Get AWS region from environment (loaded from .env)
aws_region = os.environ.get("AWS_REGION", "us-east-1")
logger.info(f"Using AWS region from .env: {aws_region}")

kb_id = get_kb_id_from_ssm()
logger.info(f"Octank Assistant runtime - KnowledgeBase ID: {kb_id}")

# Set knowledge base ID as environment variable so that Strands retrieve tool can use it
os.environ["KNOWLEDGE_BASE_ID"] = kb_id
# Set the region for the retrieve tool from .env configuration
os.environ["AWS_DEFAULT_REGION"] = aws_region
os.environ["AWS_REGION"] = aws_region
logger.info(f"Octank Assistant runtime - configured for region: {aws_region}")

# NOW import strands tools after environment is set
from strands import Agent, tool
from strands_tools import retrieve, calculator
from mock_data_generator import generate_student_data



@tool
def answer_student_questions(query: str, student_id: str = None, persona: str = "student") -> str:
    """Tool that handles student academic questions using a specialized agent.
    
    This tool provides information about:
    - Pending tasks and assignments
    - Enrolled courses and teachers
    - Current grades
    - Subjects requiring focus (grade < 5.0)
    
    Args:
        query: The student's question
        student_id: Optional student ID for personalized data
        persona: The persona type making the request (default: "student")
    
    Returns:
        String response from the educational assistant agent
    """
    global kb_id
    # Validate persona - only students should access this tool
    if persona not in ["student", "administrator"]:
        return f"Access denied: This tool is only available for student and administrator personas. Current persona: {persona}"
    
    # Generate mock student data scoped to the persona
    student_data = generate_student_data(student_id)
    
    # Format mock data for context
    mock_data = {
        "student_id": student_data.student_id,
        "student_name": student_data.student_name,
        "pending_tasks": [
            {
                "course_name": task.course_name,
                "task_id": task.task_id,
                "due_date": task.due_date
            }
            for task in student_data.pending_tasks
        ],
        "enrolled_courses": [
            {
                "course_name": course.course_name,
                "course_id": course.course_id,
                "teacher_name": course.teacher_name
            }
            for course in student_data.enrolled_courses
        ],
        "grades": [
            {
                "course_name": grade.course_name,
                "course_id": grade.course_id,
                "grade": grade.grade
            }
            for grade in student_data.grades
        ],
        "focus_areas": student_data.focus_areas
    }
    
    # Create the educational assistant agent
    educational_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        tools= [retrieve],
        system_prompt=f"""You are an Educational Assistant that helps students with academic queries.

You can provide information about:
- Pending tasks and assignments
- Enrolled courses and teachers
- Current grades
- Subjects requiring focus (grade < 5.0)
- Retrieve subject content on Knowledge bases, when a student ask for the content for the next text you MUST retrieve the content from that subject from the knowledge base configured from id {kb_id} and use retrieve tool

Use the mock data provided to answer student questions in a helpful and encouraging manner.
Be supportive and provide actionable advice when students are struggling.
Format your responses clearly and concisely.

When discussing grades:
- Grades are on a 0-10 scale
- Grades below 5.0 indicate areas needing focus
- Encourage students to seek help in challenging subjects
- search for content on the knowledge base to generate tips on what the studentshould focus

When discussing tasks:
- Prioritize tasks by due date
- Encourage time management
- Suggest breaking down complex assignments
"""
    )
    
    # Inject mock data into the query context with persona information
    context = f"""Mock Academic Data for {student_data.student_name} (ID: {student_data.student_id}):
[Requesting Persona: {persona}]

Enrolled Courses:
{_format_courses(mock_data['enrolled_courses'])}

Current Grades:
{_format_grades(mock_data['grades'])}

Pending Tasks:
{_format_tasks(mock_data['pending_tasks'])}

Focus Areas (grades < 5.0):
{', '.join(mock_data['focus_areas']) if mock_data['focus_areas'] else 'None - all grades are satisfactory!'}

Student Query: {query}
"""
    
    # Get response from the agent
    response = educational_agent(context)
    
    return str(response)


def _format_courses(courses: list) -> str:
    """Format course list for display."""
    if not courses:
        return "No enrolled courses"
    
    lines = []
    for course in courses:
        lines.append(f"  - {course['course_name']} ({course['course_id']}) - Teacher: {course['teacher_name']}")
    return "\n".join(lines)


def _format_grades(grades: list) -> str:
    """Format grades list for display."""
    if not grades:
        return "No grades available"
    
    lines = []
    for grade in grades:
        status = "⚠️ Needs Focus" if grade['grade'] < 5.0 else "✓ Good"
        lines.append(f"  - {grade['course_name']}: {grade['grade']:.1f}/10.0 {status}")
    return "\n".join(lines)


def _format_tasks(tasks: list) -> str:
    """Format tasks list for display."""
    if not tasks:
        return "No pending tasks"
    
    lines = []
    for task in tasks:
        lines.append(f"  - {task['course_name']}: {task['task_id']} (Due: {task['due_date']})")
    return "\n".join(lines)
