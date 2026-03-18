import os
import sys

# Add the project directory to sys.path to allow importing from backend
sys.path.append(os.path.dirname(__file__))

from backend.llm_service import parse_resume_with_llm

sample_resume = """
John Doe
Software Engineer
john.doe@example.com

Experience:
Senior Software Engineer at TechCorp (2018 - Present)
- Led a team of 5 engineers to deliver a new microservices architecture.
- Improved application performance by 30% using Redis caching.
- Developed backend services in Java and Python.

Software Engineer at WebSolutions (2015 - 2018)
- Built user interfaces using React and Redux.
- Maintained a legacy PHP codebase and migrated it to Node.js.

Education:
B.S. in Computer Science from University of Example, 2015

Skills:
Java, Python, Javascript, React, Node.js, SQL, AWS, Redis.
"""

print("--- Calling LLM with new prompt ---")
result = parse_resume_with_llm(sample_resume)
print("--- Result ---")
print(result)
