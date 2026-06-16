from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

    interviews = relationship(
        "Interview", back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Candidate id={self.id} name={self.name!r} email={self.email!r}>"


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    domain = Column(String(100))
    difficulty = Column(String(50))
    total_questions = Column(Integer)
    overall_score = Column(Float)
    percentage = Column(Float)
    letter_grade = Column(String(5))
    verdict = Column(String(200))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Float)
    status = Column(String(20), default="completed")

    candidate = relationship("Candidate", back_populates="interviews")
    questions = relationship(
        "InterviewQuestion", back_populates="interview", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Interview id={self.id} domain={self.domain!r} grade={self.letter_grade!r}>"


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_number = Column(Integer)
    question_text = Column(Text)
    difficulty = Column(String(50))
    topic = Column(String(100))
    candidate_answer = Column(Text)
    score = Column(Integer)
    grade = Column(String(50))
    strengths = Column(Text)
    improvements = Column(Text)
    ideal_answer_hint = Column(Text)
    time_taken_seconds = Column(Integer)

    interview = relationship("Interview", back_populates="questions")

    def __repr__(self):
        return (
            f"<InterviewQuestion id={self.id} "
            f"q={self.question_number} score={self.score}>"
        )
