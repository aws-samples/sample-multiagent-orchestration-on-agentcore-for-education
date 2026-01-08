"""Mock data generator for all agent types.

This module provides functions to generate dummy data for demonstration purposes.
All data is mock/dummy data and does not represent real users or information.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import secrets

from models.core import (
    StudentData,
    TeacherData,
    AdministratorData,
    PendingTask,
    Course,
    Grade,
    PaymentInfo,
    TeacherMetrics,
    TeacherCourseMetrics,
    LowPerformingStudent
)


# Sample data pools
STUDENT_NAMES = [
    "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa",
    "Carlos Souza", "Juliana Lima", "Rafael Alves", "Beatriz Rocha"
]

TEACHER_NAMES = [
    "Prof. Silva", "Prof. Santos", "Prof. Oliveira", "Prof. Costa",
    "Prof. Souza", "Prof. Lima", "Prof. Alves", "Prof. Rocha"
]

COURSE_NAMES = [
    "Mathematics", "Physics", "Chemistry", "Biology",
    "History", "Geography", "Literature", "English",
    "Physical Education", "Arts", "Music", "Computer Science"
]


def generate_student_data(student_id: str = None) -> StudentData:
    """Generate mock student data.
    
    Args:
        student_id: Optional student ID (generates random if not provided)
    
    Returns:
        StudentData with mock information
    """
    if student_id is None:
        student_id = f"STU-{secrets.randbelow(999) + 1:03d}"
    
    student_name = secrets.choice(STUDENT_NAMES)
    
    # Generate enrolled courses (3-6 courses)
    num_courses = secrets.randbelow(4) + 3
    selected_courses = secrets.SystemRandom().sample(COURSE_NAMES, num_courses)
    
    enrolled_courses = []
    grades = []
    pending_tasks = []
    focus_areas = []
    
    for i, course_name in enumerate(selected_courses):
        course_id = f"{course_name[:4].upper()}-{100 + i}"
        teacher_name = secrets.choice(TEACHER_NAMES)
        
        # Create course
        course = Course(
            course_id=course_id,
            course_name=course_name,
            teacher_name=teacher_name
        )
        enrolled_courses.append(course)
        
        # Create grade (0-10 scale)
        grade_value = round(secrets.SystemRandom().uniform(3.0, 10.0), 1)
        grade = Grade(
            course_id=course_id,
            course_name=course_name,
            grade=grade_value
        )
        grades.append(grade)
        
        # Add to focus areas if grade < 5.0
        if grade_value < 5.0:
            focus_areas.append(course_name)
        
        # Generate pending tasks (0-3 per course)
        num_tasks = secrets.randbelow(4)
        for j in range(num_tasks):
            due_date = date.today() + timedelta(days=secrets.randbelow(30) + 1)
            task = PendingTask(
                task_id=f"TASK-{secrets.randbelow(9000) + 1000}",
                course_name=course_name,
                course_id=course_id,
                due_date=due_date.isoformat()
            )
            pending_tasks.append(task)
    
    return StudentData(
        student_id=student_id,
        student_name=student_name,
        enrolled_courses=enrolled_courses,
        pending_tasks=pending_tasks,
        grades=grades,
        focus_areas=focus_areas
    )


def generate_teacher_data(teacher_id: str = None) -> TeacherData:
    """Generate mock teacher data.
    
    Args:
        teacher_id: Optional teacher ID (generates random if not provided)
    
    Returns:
        TeacherData with mock information
    """
    if teacher_id is None:
        teacher_id = f"TEACH-{secrets.randbelow(99) + 1:03d}"
    
    teacher_name = secrets.choice(TEACHER_NAMES)
    
    # Generate courses (2-4 courses)
    num_courses = secrets.randbelow(3) + 2
    selected_courses = secrets.SystemRandom().sample(COURSE_NAMES, num_courses)
    
    courses = []
    pending_tasks = []
    low_performers = []
    
    for i, course_name in enumerate(selected_courses):
        course_id = f"{course_name[:4].upper()}-{100 + i}"
        student_count = secrets.randbelow(21) + 15
        overdue_tasks = secrets.randbelow(6)
        
        # Create course metrics
        course_metrics = TeacherCourseMetrics(
            course_id=course_id,
            course_name=course_name,
            student_count=student_count,
            overdue_tasks=overdue_tasks
        )
        courses.append(course_metrics)
        
        # Generate pending tasks from students
        num_pending = secrets.randbelow(4)
        for j in range(num_pending):
            student_name = secrets.choice(STUDENT_NAMES)
            student_id = f"STU-{secrets.randbelow(999) + 1:03d}"
            due_date = date.today() + timedelta(days=secrets.randbelow(21) - 5)
            
            task = PendingTask(
                task_id=f"TASK-{secrets.randbelow(9000) + 1000}",
                course_name=course_name,
                course_id=course_id,
                due_date=due_date.isoformat()
            )
            pending_tasks.append(task)
        
        # Generate low-performing students (0-3 per course)
        num_low_performers = secrets.randbelow(4)
        for j in range(num_low_performers):
            student_name = secrets.choice(STUDENT_NAMES)
            student_id = f"STU-{secrets.randbelow(999) + 1:03d}"
            grade = round(secrets.SystemRandom().uniform(2.0, 4.9), 1)
            
            low_performer = LowPerformingStudent(
                student_id=student_id,
                student_name=student_name,
                course_name=course_name,
                course_id=course_id,
                grade=grade
            )
            low_performers.append(low_performer)
    
    # Sort low performers by grade (ascending)
    low_performers.sort(key=lambda x: x.grade)
    
    return TeacherData(
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        courses=courses,
        pending_tasks=pending_tasks,
        low_performers=low_performers
    )


def generate_payment_data(student_id: str = None) -> PaymentInfo:
    """Generate mock payment data.
    
    Args:
        student_id: Optional student ID (generates random if not provided)
    
    Returns:
        PaymentInfo with mock information
    """
    if student_id is None:
        student_id = f"STU-{secrets.randbelow(999) + 1:03d}"
    
    student_name = secrets.choice(STUDENT_NAMES)
    
    # Generate unpaid months (0-3 months)
    num_unpaid = secrets.randbelow(4)
    unpaid_months = []
    
    if num_unpaid > 0:
        current_date = date.today()
        for i in range(num_unpaid):
            month_date = current_date - timedelta(days=30 * (i + 1))
            month_str = month_date.strftime("%B %Y")
            unpaid_months.append(month_str)
        
        status = "overdue"
        amount_due = num_unpaid * 600.00
    else:
        status = "paid"
        amount_due = 0.0
    
    # Generate receipt ID if paid
    receipt_id = f"REC-{secrets.randbelow(90000) + 10000}" if status == "paid" else None
    
    # Get payment month
    payment_month = date.today().strftime("%B %Y")
    
    return PaymentInfo(
        student_id=student_id,
        student_name=student_name,
        unpaid_months=unpaid_months,
        amount_due=amount_due,
        payment_month=payment_month,
        status=status,
        receipt_id=receipt_id
    )


def generate_admin_data() -> AdministratorData:
    """Generate mock administrator data.
    
    Returns:
        AdministratorData with mock information
    """
    # Generate delinquent students (3-8 students)
    num_delinquent = secrets.randbelow(6) + 3
    delinquent_students = []
    
    for i in range(num_delinquent):
        payment_info = generate_payment_data()
        # Ensure they have unpaid months
        if not payment_info.unpaid_months:
            payment_info.unpaid_months = ["November 2025"]
            payment_info.amount_due = 600.00
            payment_info.status = "overdue"
        delinquent_students.append(payment_info)
    
    # Generate low-performing students (5-12 students)
    num_low_performers = secrets.randbelow(8) + 5
    low_performing_students = []
    
    for i in range(num_low_performers):
        student_name = secrets.choice(STUDENT_NAMES)
        student_id = f"STU-{secrets.randbelow(999) + 1:03d}"
        course_name = secrets.choice(COURSE_NAMES)
        course_id = f"{course_name[:4].upper()}-{secrets.randbelow(100) + 100}"
        grade = round(secrets.SystemRandom().uniform(2.0, 4.9), 1)
        
        low_performer = LowPerformingStudent(
            student_id=student_id,
            student_name=student_name,
            course_name=course_name,
            course_id=course_id,
            grade=grade
        )
        low_performing_students.append(low_performer)
    
    # Generate teacher performance metrics (4-8 teachers)
    num_teachers = secrets.randbelow(5) + 4
    teacher_performance = []
    
    for i in range(num_teachers):
        teacher_name = secrets.choice(TEACHER_NAMES)
        teacher_id = f"TEACH-{secrets.randbelow(99) + 1:03d}"
        
        classes_taught = secrets.randbelow(6) + 3
        grades_published = secrets.randbelow(16) + 5
        below_average_pct = round(secrets.SystemRandom().uniform(5.0, 25.0), 1)
        
        # Generate insights
        insights = []
        if below_average_pct < 10:
            insights.append("Excellent student performance")
        elif below_average_pct > 20:
            insights.append("High percentage of struggling students - may need support")
        
        if grades_published > 15:
            insights.append("Very active in grading")
        
        if classes_taught > 6:
            insights.append("High teaching load")
        
        if not insights:
            insights.append("Normal performance metrics")
        
        metrics = TeacherMetrics(
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            classes_taught_last_week=classes_taught,
            grades_published_last_week=grades_published,
            below_average_percentage=below_average_pct,
            insights=insights
        )
        teacher_performance.append(metrics)
    
    return AdministratorData(
        delinquent_students=delinquent_students,
        low_performing_students=low_performing_students,
        teacher_performance=teacher_performance
    )


def generate_mock_data_for_persona(persona_type: str, persona_id: str = None) -> Dict[str, Any]:
    """Generate mock data based on persona type.
    
    Args:
        persona_type: Type of persona ("student", "teacher", "administrator")
        persona_id: Optional persona ID
    
    Returns:
        Dictionary with mock data appropriate for the persona
    """
    if persona_type == "student":
        data = generate_student_data(persona_id)
        return {
            "persona_type": "student",
            "student_id": data.student_id,
            "student_name": data.student_name,
            "enrolled_courses": [
                {
                    "course_id": c.course_id,
                    "course_name": c.course_name,
                    "teacher_name": c.teacher_name
                }
                for c in data.enrolled_courses
            ],
            "pending_tasks": [
                {
                    "task_id": t.task_id,
                    "course_name": t.course_name,
                    "course_id": t.course_id,
                    "due_date": t.due_date
                }
                for t in data.pending_tasks
            ],
            "grades": [
                {
                    "course_id": g.course_id,
                    "course_name": g.course_name,
                    "grade": g.grade
                }
                for g in data.grades
            ],
            "focus_areas": data.focus_areas
        }
    
    elif persona_type == "teacher":
        data = generate_teacher_data(persona_id)
        return {
            "persona_type": "teacher",
            "teacher_id": data.teacher_id,
            "teacher_name": data.teacher_name,
            "courses": [
                {
                    "course_id": c.course_id,
                    "course_name": c.course_name,
                    "student_count": c.student_count,
                    "overdue_tasks": c.overdue_tasks
                }
                for c in data.courses
            ],
            "pending_tasks": [
                {
                    "task_id": t.task_id,
                    "course_name": t.course_name,
                    "due_date": t.due_date
                }
                for t in data.pending_tasks
            ],
            "low_performers": [
                {
                    "student_id": lp.student_id,
                    "student_name": lp.student_name,
                    "course_name": lp.course_name,
                    "grade": lp.grade
                }
                for lp in data.low_performers
            ]
        }
    
    elif persona_type == "administrator":
        data = generate_admin_data()
        return {
            "persona_type": "administrator",
            "delinquent_students": [
                {
                    "student_id": ds.student_id,
                    "student_name": ds.student_name,
                    "unpaid_months": ds.unpaid_months,
                    "amount_due": ds.amount_due
                }
                for ds in data.delinquent_students
            ],
            "low_performing_students": [
                {
                    "student_id": lp.student_id,
                    "student_name": lp.student_name,
                    "course_name": lp.course_name,
                    "grade": lp.grade
                }
                for lp in data.low_performing_students
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
                for tp in data.teacher_performance
            ]
        }
    
    else:
        raise ValueError(f"Unknown persona type: {persona_type}")
