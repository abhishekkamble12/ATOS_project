# utils/sample_data.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Realistic sample employee data generator.
Produces diverse, realistic Indian IT company workforce data for demos.
"""

import csv
import io
import random
from typing import Any

# ── 50 realistic sample employees ────────────────────────────────────────────

SAMPLE_EMPLOYEES: list[dict[str, Any]] = [
    # Engineering Department
    {"employee_id": "ENG001", "name": "Arjun Sharma",     "role": "Senior Software Engineer",   "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.88, "productivity_base": 82},
    {"employee_id": "ENG002", "name": "Priya Patel",      "role": "Tech Lead",                  "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.92, "productivity_base": 88},
    {"employee_id": "ENG003", "name": "Ravi Kumar",       "role": "Junior Developer",           "department": "Engineering", "current_tool": "Email",  "adoption_propensity": 0.75, "productivity_base": 65},
    {"employee_id": "ENG004", "name": "Sneha Iyer",       "role": "DevOps Engineer",            "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.85, "productivity_base": 78},
    {"employee_id": "ENG005", "name": "Vikram Nair",      "role": "Staff Engineer",             "department": "Engineering", "current_tool": "Teams",  "adoption_propensity": 0.91, "productivity_base": 90},
    {"employee_id": "ENG006", "name": "Ananya Desai",     "role": "QA Engineer",                "department": "Engineering", "current_tool": "Email",  "adoption_propensity": 0.62, "productivity_base": 70},
    {"employee_id": "ENG007", "name": "Karthik Reddy",    "role": "Data Engineer",              "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.83, "productivity_base": 76},
    {"employee_id": "ENG008", "name": "Meera Krishnan",   "role": "Backend Developer",          "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.79, "productivity_base": 73},
    {"employee_id": "ENG009", "name": "Suresh Venkat",    "role": "Security Engineer",          "department": "Engineering", "current_tool": "Teams",  "adoption_propensity": 0.70, "productivity_base": 80},
    {"employee_id": "ENG010", "name": "Divya Balaji",     "role": "Frontend Developer",         "department": "Engineering", "current_tool": "Slack",  "adoption_propensity": 0.87, "productivity_base": 74},

    # Product Department
    {"employee_id": "PRD001", "name": "Rahul Mehta",      "role": "Product Manager",            "department": "Product",     "current_tool": "Teams",  "adoption_propensity": 0.90, "productivity_base": 85},
    {"employee_id": "PRD002", "name": "Kavya Rao",        "role": "Senior PM",                  "department": "Product",     "current_tool": "Slack",  "adoption_propensity": 0.88, "productivity_base": 87},
    {"employee_id": "PRD003", "name": "Aditya Singh",     "role": "Product Analyst",            "department": "Product",     "current_tool": "Email",  "adoption_propensity": 0.72, "productivity_base": 71},
    {"employee_id": "PRD004", "name": "Pooja Gupta",      "role": "UX Designer",                "department": "Product",     "current_tool": "Figma",  "adoption_propensity": 0.95, "productivity_base": 89},
    {"employee_id": "PRD005", "name": "Nikhil Joshi",     "role": "Business Analyst",           "department": "Product",     "current_tool": "Teams",  "adoption_propensity": 0.78, "productivity_base": 75},

    # Sales Department
    {"employee_id": "SAL001", "name": "Amit Verma",       "role": "Sales Director",             "department": "Sales",       "current_tool": "Teams",  "adoption_propensity": 0.65, "productivity_base": 83},
    {"employee_id": "SAL002", "name": "Sunita Pillai",    "role": "Account Executive",          "department": "Sales",       "current_tool": "Email",  "adoption_propensity": 0.58, "productivity_base": 77},
    {"employee_id": "SAL003", "name": "Rajesh Tiwari",    "role": "Business Development",       "department": "Sales",       "current_tool": "Email",  "adoption_propensity": 0.52, "productivity_base": 72},
    {"employee_id": "SAL004", "name": "Deepika Nambiar",  "role": "Sales Engineer",             "department": "Sales",       "current_tool": "Teams",  "adoption_propensity": 0.74, "productivity_base": 80},
    {"employee_id": "SAL005", "name": "Pranav Shah",      "role": "Inside Sales",               "department": "Sales",       "current_tool": "Email",  "adoption_propensity": 0.61, "productivity_base": 68},

    # HR Department
    {"employee_id": "HR001",  "name": "Shalini Goyal",    "role": "HR Director",                "department": "HR",          "current_tool": "Teams",  "adoption_propensity": 0.82, "productivity_base": 79},
    {"employee_id": "HR002",  "name": "Vivek Saxena",     "role": "HR Business Partner",        "department": "HR",          "current_tool": "Email",  "adoption_propensity": 0.68, "productivity_base": 73},
    {"employee_id": "HR003",  "name": "Rekha Subramaniam","role": "Talent Acquisition",         "department": "HR",          "current_tool": "Teams",  "adoption_propensity": 0.77, "productivity_base": 75},
    {"employee_id": "HR004",  "name": "Arun Chandrasekar","role": "L&D Specialist",             "department": "HR",          "current_tool": "Slack",  "adoption_propensity": 0.84, "productivity_base": 71},

    # Finance Department
    {"employee_id": "FIN001", "name": "Subramaniam Iyer", "role": "CFO",                        "department": "Finance",     "current_tool": "Email",  "adoption_propensity": 0.42, "productivity_base": 86},
    {"employee_id": "FIN002", "name": "Preeti Malhotra",  "role": "Finance Manager",            "department": "Finance",     "current_tool": "Email",  "adoption_propensity": 0.48, "productivity_base": 80},
    {"employee_id": "FIN003", "name": "Vinod Kumari",     "role": "Financial Analyst",          "department": "Finance",     "current_tool": "Email",  "adoption_propensity": 0.55, "productivity_base": 74},
    {"employee_id": "FIN004", "name": "Latha Srinivasan", "role": "Accounts Manager",           "department": "Finance",     "current_tool": "Teams",  "adoption_propensity": 0.63, "productivity_base": 77},

    # Operations Department
    {"employee_id": "OPS001", "name": "Mohan Krishnamurthy","role": "VP Operations",            "department": "Operations",  "current_tool": "Teams",  "adoption_propensity": 0.71, "productivity_base": 84},
    {"employee_id": "OPS002", "name": "Shweta Pandey",    "role": "Operations Manager",         "department": "Operations",  "current_tool": "Teams",  "adoption_propensity": 0.76, "productivity_base": 79},
    {"employee_id": "OPS003", "name": "Rajiv Menon",      "role": "Process Analyst",            "department": "Operations",  "current_tool": "Email",  "adoption_propensity": 0.59, "productivity_base": 70},
    {"employee_id": "OPS004", "name": "Anjali Bose",      "role": "Supply Chain Lead",          "department": "Operations",  "current_tool": "Slack",  "adoption_propensity": 0.80, "productivity_base": 76},

    # Data Science Department
    {"employee_id": "DS001",  "name": "Dhruv Banerjee",   "role": "Lead Data Scientist",        "department": "Data Science","current_tool": "Slack",  "adoption_propensity": 0.93, "productivity_base": 91},
    {"employee_id": "DS002",  "name": "Ishita Chakraborty","role": "ML Engineer",               "department": "Data Science","current_tool": "Slack",  "adoption_propensity": 0.91, "productivity_base": 88},
    {"employee_id": "DS003",  "name": "Siddharth Mukherjee","role": "Data Analyst",             "department": "Data Science","current_tool": "Email",  "adoption_propensity": 0.78, "productivity_base": 79},
    {"employee_id": "DS004",  "name": "Nandini Roy",      "role": "AI Research Engineer",       "department": "Data Science","current_tool": "Slack",  "adoption_propensity": 0.96, "productivity_base": 94},

    # Customer Success Department
    {"employee_id": "CS001",  "name": "Varun Aggarwal",   "role": "CS Director",                "department": "Customer Success","current_tool": "Teams","adoption_propensity": 0.80, "productivity_base": 82},
    {"employee_id": "CS002",  "name": "Tanvi Kapoor",     "role": "Customer Success Manager",   "department": "Customer Success","current_tool": "Teams","adoption_propensity": 0.75, "productivity_base": 78},
    {"employee_id": "CS003",  "name": "Rohan Mishra",     "role": "Support Engineer",           "department": "Customer Success","current_tool": "Email","adoption_propensity": 0.66, "productivity_base": 70},
    {"employee_id": "CS004",  "name": "Swati Bajaj",      "role": "Implementation Specialist",  "department": "Customer Success","current_tool": "Teams","adoption_propensity": 0.73, "productivity_base": 74},

    # Marketing Department
    {"employee_id": "MKT001", "name": "Hardik Solanki",   "role": "Marketing Director",         "department": "Marketing",   "current_tool": "Slack",  "adoption_propensity": 0.86, "productivity_base": 81},
    {"employee_id": "MKT002", "name": "Riya Chandra",     "role": "Content Strategist",         "department": "Marketing",   "current_tool": "Slack",  "adoption_propensity": 0.89, "productivity_base": 77},
    {"employee_id": "MKT003", "name": "Sameer Dixit",     "role": "Growth Hacker",              "department": "Marketing",   "current_tool": "Slack",  "adoption_propensity": 0.92, "productivity_base": 83},

    # Infrastructure / Cloud
    {"employee_id": "INF001", "name": "Bharat Narayanan", "role": "Cloud Architect",            "department": "Infrastructure","current_tool": "Slack", "adoption_propensity": 0.88, "productivity_base": 87},
    {"employee_id": "INF002", "name": "Chitra Suresh",    "role": "SRE / Platform Engineer",   "department": "Infrastructure","current_tool": "Slack", "adoption_propensity": 0.84, "productivity_base": 84},
    {"employee_id": "INF003", "name": "Gaurav Tripathi",  "role": "Network Engineer",           "department": "Infrastructure","current_tool": "Email", "adoption_propensity": 0.60, "productivity_base": 72},
]


def generate_sample_csv_bytes() -> bytes:
    """
    Generates the sample employees CSV as UTF-8 bytes.
    Can be returned directly as a file download response.
    """
    output = io.StringIO()
    fieldnames = [
        "employee_id", "name", "role", "department",
        "current_tool", "adoption_propensity", "productivity_base",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for emp in SAMPLE_EMPLOYEES:
        writer.writerow({k: emp[k] for k in fieldnames})

    return output.getvalue().encode("utf-8")


def get_sample_employees_dicts() -> list[dict[str, Any]]:
    """Returns the raw sample employee list (for testing / seeding)."""
    return [dict(e) for e in SAMPLE_EMPLOYEES]
