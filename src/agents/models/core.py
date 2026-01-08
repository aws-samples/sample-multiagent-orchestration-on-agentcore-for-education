"""Core data models for the multi-agent system."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Dict, Any, Optional


@dataclass
class PersonaContext:
    """Context for a user persona."""
    persona_type: str  # "student" | "teacher" | "administrator"
    persona_id: str
    persona_name: str
    query_timestamp: datetime


@dataclass
class PendingTask:
    """A pending task/assignment."""
    task_id: str
    course_name: str
    course_id: str
    due_date: str  # ISO 8601 format


@dataclass
class Course:
    """Course enrollment information."""
    course_id: str
    course_name: str
    teacher_name: str


@dataclass
class Grade:
    """Student grade for a course."""
    course_id: str
    course_name: str
    grade: float  # 0-10 scale


@dataclass
class StudentData:
    """Complete student data structure."""
    student_id: str
    student_name: str
    enrolled_courses: List[Course]
    pending_tasks: List[PendingTask]
    grades: List[Grade]
    focus_areas: List[str]  # Courses with grade < 5.0


@dataclass
class TeacherCourseMetrics:
    """Metrics for a teacher's course."""
    course_id: str
    course_name: str
    student_count: int
    overdue_tasks: int


@dataclass
class LowPerformingStudent:
    """Student with low performance."""
    student_id: str
    student_name: str
    course_name: str
    course_id: str
    grade: float


@dataclass
class TeacherData:
    """Complete teacher data structure."""
    teacher_id: str
    teacher_name: str
    courses: List[TeacherCourseMetrics]
    pending_tasks: List[PendingTask]
    low_performers: List[LowPerformingStudent]


@dataclass
class PaymentInfo:
    """Payment information."""
    student_id: str
    student_name: Optional[str]
    unpaid_months: List[str]
    amount_due: float
    payment_month: Optional[str]
    status: str  # "paid" | "pending" | "overdue"
    receipt_id: Optional[str]


@dataclass
class TeacherMetrics:
    """Teacher performance metrics."""
    teacher_id: str
    teacher_name: str
    classes_taught_last_week: int
    grades_published_last_week: int
    below_average_percentage: float
    insights: List[str]


@dataclass
class AdministratorData:
    """Complete administrator data structure."""
    delinquent_students: List[PaymentInfo]
    low_performing_students: List[LowPerformingStudent]
    teacher_performance: List[TeacherMetrics]
