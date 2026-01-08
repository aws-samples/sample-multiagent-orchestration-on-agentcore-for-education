"""Financial Assistant Agent - handles payment and financial queries.

This agent is exposed as a tool that can be invoked by the orchestrator.
It returns dummy data for demonstration purposes.
"""

from strands import Agent, tool
from typing import Dict, Any

from mock_data_generator import generate_payment_data


@tool
def answer_payment_questions(query: str, student_id: str = None, persona: str = "student") -> str:
    """Tool that handles payment and financial questions using a specialized agent.
    
    This tool provides information about:
    - Pending payments and overdue amounts
    - Recent payment history
    - Payment receipt status
    - Payment processing simulations
    
    Args:
        query: The payment-related question
        student_id: Optional student ID for personalized payment data
        persona: The persona type making the request (default: "student")
    
    Returns:
        String response from the financial assistant agent
    """
    
    # All personas can access payment information
    # Students see their own data, administrators see all data
    
    # Generate mock payment data scoped to the persona
    payment_data = generate_payment_data(student_id)
    
    # Format mock data for context
    mock_data = {
        "student_id": payment_data.student_id,
        "student_name": payment_data.student_name,
        "unpaid_months": payment_data.unpaid_months,
        "amount_due": payment_data.amount_due,
        "payment_month": payment_data.payment_month,
        "status": payment_data.status,
        "receipt_id": payment_data.receipt_id
    }
    
    # Create the financial assistant agent
    financial_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        system_prompt="""You are a Financial Assistant that helps with payment queries.

You can provide information about:
- Pending payments and overdue amounts
- Recent payment history
- Payment receipt status
- Payment processing simulations

Use the mock data provided to answer payment questions clearly and professionally.
Be helpful and provide actionable information about payment status.
Format your responses clearly and concisely.

When discussing payments:
- Monthly tuition is 600.00 per month
- Payments are due on the 1st of each month
- Overdue payments may incur late fees
- Receipt IDs are provided for completed payments

When discussing payment status:
- "paid" means all payments are current
- "pending" means payment is due soon
- "overdue" means payment is past due

When simulating receipt processing:
- Acknowledge receipt upload
- Provide mock confirmation with receipt ID
- Indicate successful processing
"""
    )
    
    # Inject mock data into the query context with persona information
    context = f"""Mock Payment Data for {payment_data.student_name} (ID: {payment_data.student_id}):
[Requesting Persona: {persona}]

Payment Status: {payment_data.status.upper()}
Current Month: {payment_data.payment_month}

{_format_payment_status(mock_data)}

Payment Query: {query}
"""
    
    # Get response from the agent
    response = financial_agent(context)
    
    return str(response)


def _format_payment_status(payment_data: dict) -> str:
    """Format payment status for display."""
    lines = []
    
    if payment_data['status'] == 'paid':
        lines.append("✓ All payments are current!")
        if payment_data['receipt_id']:
            lines.append(f"  Last Receipt ID: {payment_data['receipt_id']}")
        lines.append(f"  Amount Due: ${payment_data['amount_due']:.2f}")
    
    elif payment_data['status'] == 'overdue':
        lines.append("⚠️ OVERDUE PAYMENTS")
        lines.append(f"  Unpaid Months: {', '.join(payment_data['unpaid_months'])}")
        lines.append(f"  Total Amount Due: ${payment_data['amount_due']:.2f}")
        lines.append(f"  Monthly Rate: $600.00")
    
    elif payment_data['status'] == 'pending':
        lines.append("⏳ Payment Pending")
        lines.append(f"  Amount Due: ${payment_data['amount_due']:.2f}")
        lines.append(f"  Due Date: 1st of {payment_data['payment_month']}")
    
    return "\n".join(lines)
