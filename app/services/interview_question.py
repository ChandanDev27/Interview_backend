from app.schemas.interview_question import QuestionModel
from app.config import logger
from typing import List
from pymongo import IndexModel, ASCENDING
from pydantic import ValidationError


class QuestionService:

    @staticmethod
    async def seed_questions(db):
        questions_data = [
            {"category": "General", "question": "Tell me about yourself."},
            {
                "category": "General",
                "question": "Why do you want to work for this company?"
            },
            {
                "category": "General",
                "question": "What are your strengths and weaknesses?"
                },
            {
                "category": "General",
                "question": "Where do you see yourself in five years?"
                },
            {
                "category": "General",
                "question": "Why should we hire you?"
                },
            {
                "category": "General",
                "question": "What do you know about our company?"
                },
            {
                "category": "General",
                "question": (
                    "Can you describe a time when you faced a challenge at work "
                    "and how you handled it?"
                    ),
                },
            {"category": "General", "question": "What motivates you?"},
            {"category": "General", "question": "How do you handle stress and pressure?"},
            {"category": "Behavioral", "question": "Tell me about a time when you worked in a team."},
            {"category": "Behavioral", "question": "Describe a situation where you had a conflict at work and how you resolved it."},
            {"category": "Behavioral", "question": "Give an example of a time you took initiative."},
            {"category": "Behavioral", "question": "Tell me about a time you failed and what you learned from it."},
            {"category": "Behavioral", "question": "Describe a time you had to meet a tight deadline."},
            {"category": "Technical", "question": "What experience do you have in this field?"},
            {"category": "Technical", "question": "What tools/software are you proficient in?"},
            {"category": "Technical", "question": "Can you walk me through a project you have worked on?"},
            {"category": "Technical", "question": "How do you stay updated with industry trends?"},
            {"category": "Technical", "question": "What additional certifications or training have you completed?"},
            {"category": "Situational", "question": "How would you handle an unhappy client?"},
            {"category": "Situational", "question": "What would you do if you had multiple urgent deadlines at the same time?"},
            {"category": "Situational", "question": "How do you prioritize tasks in a busy work environment?"},
            {"category": "Situational", "question": "If you were given a project outside of your expertise, how would you approach it?"},
            {"category": "General", "question": "How has your academic background prepared you for this job?", "experience_level": "fresher"},
            {"category": "General", "question": "What internships or projects have you worked on?", "experience_level": "fresher"},
            {"category": "General", "question": "How do you plan to learn and grow in this industry?", "experience_level": "fresher"},
            # Experienced-specific questions
            {"category": "General", "question": "Tell us about your previous work experience and key achievements.", "experience_level": "experienced"},
            {"category": "General", "question": "How have you handled conflicts in the workplace?", "experience_level": "experienced"},
            {"category": "General", "question": "Describe a time you led a team or project.", "experience_level": "experienced"},
            {
                "category": "Behavioral",
                "question": "Tell me about a project you completed successfully.",
                "experience_level": "both",
                "tips": "Use the STAR technique: Situation, Task, Action, Result.",
                "example_answer": "I was leading a project with a tight deadline. Two team members were unavailable, "
                "so I redistributed tasks, used UpWork to outsource some work, "
                "and ensured communication was clear. As a result, we delivered the project on time without compromising quality."
            },
            {
                "category": "General",
                "question": "Why are you leaving your current job?",
                "experience_level": "experienced"
                },
            {
                "category": "Technical",
                "question": "What experience do you have in this field?",
                "experience_level": "experienced",
                "tips": "Mention specific projects, technologies, and impact. Focus on achievements rather than just listing skills.",
                "example_answer": "I have 3 years of experience in backend development, "
                "primarily with FastAPI and MongoDB. One of my key projects involved optimizing API response times, which improved performance by 40%."
            },
            {
                "category": "General",
                "question": "Why did you decide to become a Software Engineer?",
                "experience_level": "both",
                "tips": "Talk about how your passion for this type of work goes back many years, and how you thrive in solving complex problems.",
                "example_answer": "I've always been fascinated by technology. As a child, I enjoyed solving puzzles, "
                "and coding felt like a natural extension of that. Over time, I realized software engineering allows me to create impactful solutions, and that’s what excites me the most."
            },
            {
                "category": "Situational",
                "question": "What would you do if you had multiple urgent deadlines at the same time?",
                "experience_level": "both",
                "tips": "Demonstrate prioritization, communication, and time management skills.",
                "example_answer": "I would evaluate the urgency and impact of each task, discuss priorities with stakeholders, "
                "and break down work into manageable steps. I’d also delegate where possible to ensure all deadlines are met efficiently."
            },
            {
                "category": "General",
                "question": "What experience do you have in this field?",
                "experience_level": "fresher",
                "tips": "Show enthusiasm and willingness to learn.",
                "example_answer": "I may not have direct industry experience, but my [academic achievements, "
                "project work, or certifications] have prepared me to take on real-world challenges OR "
                "I am eager to leverage my skills and grow within the organization while contributing to its success."
            },
            {
                "category": "General",
                "experience_level": "both",
                "question": "Tell me about a project you completed successfully.",
                "tips": [
                    "This question assesses your ability to complete software engineering projects successfully.",
                    "Give a specific situation where you had to overcome an unexpected problem to complete a project on time.",
                    "Use the STAR technique to structure your answer."
                    ],
                "example_answer": "SITUATION: I was working on a time-sensitive software engineering project where two team members went off sick."
                " TASK: I had to come up with a new plan to complete the project. "
                "ACTION: I suggested redistributing tasks and outsourcing some work. RESULT: The project was completed on time and to a high standard."
            },
            {
                "category": "Behavioral",
                "experience_level": "both",
                "question": "Can you describe a time when you faced a challenge at work and how you handled it?",
                "tips": [
                    "Use the STAR method (Situation, Task, Action, Result) to structure your answer.",
                    "Describe a real challenge, how you approached it, and the successful outcome.",
                    "Show problem-solving skills and resilience."
                    ],
                "example_answer": "SITUATION: A critical system crashed before a product launch. "
                "TASK: I needed to find a quick solution to fix the issue. "
                "ACTION: I coordinated with IT, identified the root cause, and implemented a fix. "
                "RESULT: The system was restored within hours, ensuring the launch stayed on track."
            },
            {
                "category": "Technical",
                "experience_level": "both",
                "question": "What are the most important skills and qualities needed to be a great Software Engineer?",
                "tips": [
                    "Mention both technical and soft skills.",
                    "Highlight problem-solving, teamwork, and continuous learning.",
                    "Provide real-world examples if possible."
                    ],
                "example_answer": "To be effective as a software engineer, you need strong coding, debugging, "
                "and problem-solving skills. Teamwork, communication, and a passion for learning are equally important."
            },
            {
                "category": "Career Motivation",
                "experience_level": "both",
                "question": "Why do you want to work for this company?",
                "tips": [
                    "Show that you have researched the company.",
                    "Mention specific aspects you admire (culture, mission, innovation).",
                    "Connect your skills and career goals with what the company offers."
                    ],
                "example_answer": "I admire your company’s commitment to sustainability and innovation. Your recent expansion into AI-driven solutions aligns with my background in AI,"
                " and I’d love to contribute to your mission."
            },
            {
                "category": "Self-Awareness",
                "experience_level": "both",
                "question": "What are your strengths and weaknesses?",
                "tips": [
                    "Choose a strength that is relevant to the job.",
                    "For weaknesses, pick one that isn’t a deal-breaker and show how you’re improving it.",
                    "Keep your answer professional and constructive."
                    ],
                "example_answer": "Strength: I excel at problem-solving and have improved operational efficiency in my previous roles. "
                "Weakness: I used to struggle with delegating tasks, but I’ve learned to trust my team and focus on leadership."
            }
        ]

        valid_questions = []
        for data in questions_data:
            try:
                valid_q = QuestionModel(**data)
                valid_questions.append(valid_q.dict())
            except ValidationError as e:
                logger.error(f"❌ Validation error in question: {data.get('question', 'Unknown')}. Error: {e}")

        if valid_questions:
            try:
                existing_count = await db["questions"].estimated_document_count()
                if existing_count == 0:
                    await db["questions"].insert_many(valid_questions)
                    logger.info("✅ Questions seeded successfully.")
                else:
                    logger.warning("⚠️ Questions already exist in the database. Skipping seeding.")
            except Exception as e:
                logger.error(f"⚠️ Database error while seeding questions: {e}", exc_info=True)
                raise

    @staticmethod
    async def get_questions_by_experience(db, experience_level: str) -> List[dict]:
        """Fetches interview questions based on experience level (fresher, experienced, both)."""
        query = {"$or": [{"experience_level": experience_level}, {"experience_level": "both"}]}
        questions = await db["questions"].find(query, {"_id": 0}).to_list(length=None)
        return questions

    @staticmethod
    async def create_indexes(db):
        """Ensures indexes for faster queries."""
        try:
            await db["questions"].create_indexes([
                IndexModel([("experience_level", ASCENDING)]),
                IndexModel([("category", ASCENDING)])
            ])
            logger.info("✅ Indexes created successfully.")
        except Exception as e:
            logger.error(f"⚠️ Failed to create indexes: {e}")
