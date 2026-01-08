"""Virtual Secretary Agent - handles administrative operational queries.

This agent is exposed as a tool that can be invoked by the orchestrator.
It returns dummy data for demonstration purposes.
"""

from strands import Agent, tool
from typing import Dict, Any

from mock_data_generator import generate_admin_data


@tool
def answer_admin_questions(query: str, persona: str = "administrator") -> str:
    """Tool that handles administrative operational questions using a specialized agent.
    
    This tool provides information about:
    - Delinquent student payments
    - Low-performing students across all courses
    - Teacher performance metrics
    - Operational insights and recommendations
    
    Args:
        query: The administrator's question
        persona: The persona type making the request (default: "administrator")
    
    Returns:
        String response from the virtual secretary agent
    """
    
    # Validate persona - only administrators should access this tool
    if persona != "administrator":
        return f"Access denied: This tool is only available for administrator personas. Current persona: {persona}"
    
    # Generate mock administrator data (full system scope)
    admin_data = generate_admin_data()
    
    # Format mock data for context
    mock_data = {
        "delinquent_students": [
            {
                "student_id": ds.student_id,
                "student_name": ds.student_name,
                "unpaid_months": ds.unpaid_months,
                "total_due": ds.amount_due
            }
            for ds in admin_data.delinquent_students
        ],
        "low_performing_students": [
            {
                "student_id": lp.student_id,
                "student_name": lp.student_name,
                "course_name": lp.course_name,
                "course_id": lp.course_id,
                "grade": lp.grade
            }
            for lp in admin_data.low_performing_students
        ],
        "teacher_performance": [
            {
                "teacher_id": tp.teacher_id,
                "teacher_name": tp.teacher_name,
                "classes_taught_last_week": tp.classes_taught_last_week,
                "grades_published_last_week": tp.grades_published_last_week,
                "below_average_percentage": tp.below_average_percentage,
                "insights": tp.insights
            }
            for tp in admin_data.teacher_performance
        ]
    }
    
    # Create the virtual secretary agent
    admin_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        system_prompt="""You are a Virtual Secretary that provides operational reports to administrators.

You can provide information about:
- Delinquent student payments
- Low-performing students across all courses
- Teacher performance metrics
- Operational insights and recommendations

Use the mock data provided to answer administrative questions comprehensively.
Be professional and provide actionable insights for school management.
Format your responses clearly and concisely.

When discussing delinquent payments:
- Monthly tuition is 600.00 per month
- Highlight students with multiple unpaid months
- Calculate total outstanding amounts
- Suggest follow-up actions

When discussing student performance:
- Grades are on a 0-10 scale
- Grades below 5.0 indicate students needing intervention
- Identify patterns across courses
- Suggest support programs or interventions

When discussing teacher performance:
- Highlight teachers with high workloads
- Recognize teachers with excellent student outcomes
- Identify teachers who may need support
- Provide balanced, constructive insights

When providing operational insights:
- Synthesize data across all areas
- Identify trends and patterns
- Prioritize action items
- Provide strategic recommendations
"""
    )
    
    # Inject mock data into the query context with persona information
    context = f"""Mock Administrative Data:
[Requesting Persona: {persona}]
[Access Level: Full System Scope]

=== DELINQUENT STUDENTS (Payment Issues) ===
{_format_delinquent_students(mock_data['delinquent_students'])}

=== LOW-PERFORMING STUDENTS (Academic Issues) ===
{_format_low_performing_students(mock_data['low_performing_students'])}

=== TEACHER PERFORMANCE METRICS ===
{_format_teacher_performance(mock_data['teacher_performance'])}

Administrator Query: {query}
"""
    
    # Get response from the agent
    response = admin_agent(context)
    
    return str(response)


def _format_delinquent_students(delinquent_students: list) -> str:
    """Format delinquent students list for display."""
    if not delinquent_students:
        return "No delinquent students - all payments are current!"
    
    lines = []
    total_outstanding = 0.0
    
    for ds in delinquent_students:
        lines.append(
            f"  ⚠️ {ds['student_name']} ({ds['student_id']})"
        )
        lines.append(
            f"     Unpaid Months: {', '.join(ds['unpaid_months'])}"
        )
        lines.append(
            f"     Amount Due: ${ds['total_due']:.2f}"
        )
        lines.append("")
        total_outstanding += ds['total_due']
    
    lines.append(f"TOTAL OUTSTANDING: ${total_outstanding:.2f}")
    lines.append(f"Number of Delinquent Students: {len(delinquent_students)}")
    
    return "\n".join(lines)


def _format_low_performing_students(low_performers: list) -> str:
    """Format low-performing students list for display."""
    if not low_performers:
        return "No students with grades below 5.0 - excellent academic performance!"
    
    lines = []
    
    # Group by student
    student_courses = {}
    for lp in low_performers:
        student_key = f"{lp['student_name']} ({lp['student_id']})"
        if student_key not in student_courses:
            student_courses[student_key] = []
        student_courses[student_key].append({
            'course': lp['course_name'],
            'grade': lp['grade']
        })
    
    for student, courses in student_courses.items():
        lines.append(f"  ⚠️ {student}")
        for course_info in courses:
            lines.append(
                f"     - {course_info['course']}: {course_info['grade']:.1f}/10.0"
            )
        lines.append("")
    
    lines.append(f"Total Students Needing Support: {len(student_courses)}")
    lines.append(f"Total Course Failures: {len(low_performers)}")
    
    return "\n".join(lines)


def _format_teacher_performance(teacher_metrics: list) -> str:
    """Format teacher performance metrics for display."""
    if not teacher_metrics:
        return "No teacher performance data available"
    
    lines = []
    
    for tm in teacher_metrics:
        lines.append(f"  📊 {tm['teacher_name']} ({tm['teacher_id']})")
        lines.append(f"     Classes Taught (Last Week): {tm['classes_taught_last_week']}")
        lines.append(f"     Grades Published (Last Week): {tm['grades_published_last_week']}")
        lines.append(f"     Students Below Average: {tm['below_average_percentage']:.1f}%")
        
        if tm['insights']:
            lines.append(f"     Insights:")
            for insight in tm['insights']:
                lines.append(f"       • {insight}")
        
        lines.append("")
    
    # Calculate summary statistics
    avg_classes = sum(tm['classes_taught_last_week'] for tm in teacher_metrics) / len(teacher_metrics)
    avg_grades = sum(tm['grades_published_last_week'] for tm in teacher_metrics) / len(teacher_metrics)
    avg_below = sum(tm['below_average_percentage'] for tm in teacher_metrics) / len(teacher_metrics)
    
    lines.append("=== SUMMARY STATISTICS ===")
    lines.append(f"Average Classes Taught: {avg_classes:.1f}")
    lines.append(f"Average Grades Published: {avg_grades:.1f}")
    lines.append(f"Average Below-Average Rate: {avg_below:.1f}%")
    lines.append(f"Total Teachers: {len(teacher_metrics)}")
    
    return "\n".join(lines)
