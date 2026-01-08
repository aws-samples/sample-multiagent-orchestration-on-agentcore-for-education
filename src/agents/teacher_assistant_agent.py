"""Teacher Assistant Agent - handles teacher course management queries.

This agent is exposed as a tool that can be invoked by the orchestrator.
It returns dummy data for demonstration purposes.
"""

from strands import Agent, tool
from typing import Dict, Any

from mock_data_generator import generate_teacher_data


@tool
def answer_teacher_questions(query: str, teacher_id: str = None, persona: str = "teacher") -> str:
    """Tool that handles teacher course management questions using a specialized agent.
    
    This tool provides information about:
    - Course metrics (student counts, overdue tasks)
    - Pending tasks from students
    - Low-performing students (grade < 5.0)
    - Course subjects taught
    
    Args:
        query: The teacher's question
        teacher_id: Optional teacher ID for personalized data
        persona: The persona type making the request (default: "teacher")
    
    Returns:
        String response from the teacher assistant agent
    """
    
    # Validate persona - only teachers and administrators should access this tool
    if persona not in ["teacher", "administrator"]:
        return f"Access denied: This tool is only available for teacher and administrator personas. Current persona: {persona}"
    
    # Generate mock teacher data scoped to the persona
    teacher_data = generate_teacher_data(teacher_id)
    
    # Format mock data for context
    mock_data = {
        "teacher_id": teacher_data.teacher_id,
        "teacher_name": teacher_data.teacher_name,
        "courses": [
            {
                "course_id": course.course_id,
                "course_name": course.course_name,
                "student_count": course.student_count,
                "overdue_tasks": course.overdue_tasks
            }
            for course in teacher_data.courses
        ],
        "pending_tasks": [
            {
                "task_id": task.task_id,
                "course_name": task.course_name,
                "course_id": task.course_id,
                "due_date": task.due_date
            }
            for task in teacher_data.pending_tasks
        ],
        "low_performers": [
            {
                "student_id": lp.student_id,
                "student_name": lp.student_name,
                "course_name": lp.course_name,
                "course_id": lp.course_id,
                "grade": lp.grade
            }
            for lp in teacher_data.low_performers
        ]
    }
    
    # Create the teacher assistant agent
    teacher_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        system_prompt="""You are a Teacher Assistant that helps teachers manage their courses.

You can provide information about:
- Course metrics (student counts, overdue tasks)
- Pending tasks from students
- Low-performing students (grade < 5.0)
- Course subjects taught

Use the mock data provided to answer teacher questions professionally.
Be supportive and provide actionable insights for course management.
Format your responses clearly and concisely.

When discussing student performance:
- Grades are on a 0-10 scale
- Grades below 5.0 indicate students needing additional support
- Suggest intervention strategies for struggling students
- Highlight positive trends when present

When discussing tasks:
- Prioritize overdue tasks
- Suggest strategies for improving task completion rates
- Encourage proactive communication with students

When discussing course metrics:
- Provide context for the numbers
- Suggest areas for improvement
- Celebrate successes
"""
    )
    
    # Inject mock data into the query context with persona information
    context = f"""Mock Teacher Data for {teacher_data.teacher_name} (ID: {teacher_data.teacher_id}):
[Requesting Persona: {persona}]

Courses Taught:
{_format_courses(mock_data['courses'])}

Pending Tasks from Students:
{_format_pending_tasks(mock_data['pending_tasks'])}

Low-Performing Students (grade < 5.0):
{_format_low_performers(mock_data['low_performers'])}

Teacher Query: {query}
"""
    
    # Get response from the agent
    response = teacher_agent(context)
    
    return str(response)


def _format_courses(courses: list) -> str:
    """Format course list for display."""
    if not courses:
        return "No courses assigned"
    
    lines = []
    for course in courses:
        lines.append(
            f"  - {course['course_name']} ({course['course_id']}): "
            f"{course['student_count']} students, {course['overdue_tasks']} overdue tasks"
        )
    return "\n".join(lines)


def _format_pending_tasks(tasks: list) -> str:
    """Format pending tasks list for display."""
    if not tasks:
        return "No pending tasks from students"
    
    lines = []
    for task in tasks:
        lines.append(
            f"  - {task['course_name']}: Task {task['task_id']} (Due: {task['due_date']})"
        )
    return "\n".join(lines)


def _format_low_performers(low_performers: list) -> str:
    """Format low-performing students list for display."""
    if not low_performers:
        return "No students with grades below 5.0 - excellent work!"
    
    lines = []
    for lp in low_performers:
        lines.append(
            f"  - {lp['student_name']} ({lp['student_id']}): "
            f"{lp['course_name']} - Grade: {lp['grade']:.1f}/10.0 ⚠️"
        )
    return "\n".join(lines)
