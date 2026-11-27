"""
Seed Demo Data Script for LeaderShipApp.

Creates:
1. Platform Owner (Manager): manager@company.com / Password123!
2. Executive Coach (Admin): coach@company.com / Password123!
3. Executive Coachee (User): coachee@company.com / Password123! (assigned to coach@company.com)
4. Client 360 Dossier (ClientMemoryProfile)
5. Active Client Goals (ClientGoal)
6. Sample Socratic Coaching Conversation & Messages with full telemetry & USD costs

Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
from datetime import datetime, timezone
import sys
import uuid

from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.client_goal import ClientGoal
from app.models.client_memory_profile import ClientMemoryProfile
from app.utils.security import has_password


async def seed_data() -> None:
    print("🌱 Seeding LeaderShipApp Demo Data...")
    async with AsyncSessionLocal() as session:
        # 1. Create or retrieve Platform Owner (Manager)
        res_manager = await session.execute(select(User).where(User.email == "manager@company.com"))
        manager = res_manager.scalar_one_or_none()
        if not manager:
            manager = User(
                email="manager@company.com",
                full_name="Alex Rivera (Platform Owner)",
                hashed_password=has_password("Password123!"),
                role="manager",
                password_login_enabled=True,
            )
            session.add(manager)
            await session.flush()
            print("  ✅ Created Manager: manager@company.com")
        else:
            print("  ℹ️  Manager already exists: manager@company.com")

        # 2. Create or retrieve Executive Coach (Admin)
        res_coach = await session.execute(select(User).where(User.email == "coach@company.com"))
        coach = res_coach.scalar_one_or_none()
        if not coach:
            coach = User(
                email="coach@company.com",
                full_name="Dr. Sarah Jenkins (Executive Coach)",
                hashed_password=has_password("Password123!"),
                role="admin",
                password_login_enabled=True,
            )
            session.add(coach)
            await session.flush()
            print("  ✅ Created Coach: coach@company.com")
        else:
            print("  ℹ️  Coach already exists: coach@company.com")

        # 3. Create or retrieve Coachee (User) assigned to Dr. Sarah Jenkins
        res_coachee = await session.execute(select(User).where(User.email == "coachee@company.com"))
        coachee = res_coachee.scalar_one_or_none()
        if not coachee:
            coachee = User(
                email="coachee@company.com",
                full_name="Marcus Vance (VP of Engineering)",
                hashed_password=has_password("Password123!"),
                role="user",
                assigned_coach_id=coach.id,
                password_login_enabled=True,
            )
            session.add(coachee)
            await session.flush()
            print(f"  ✅ Created Coachee: coachee@company.com (Assigned to Coach #{coach.id})")
        else:
            coachee.assigned_coach_id = coach.id
            print(f"  ℹ️  Coachee already exists: coachee@company.com")

        # 4. Create Client 360 Memory Profile
        res_profile = await session.execute(
            select(ClientMemoryProfile).where(ClientMemoryProfile.user_id == coachee.id)
        )
        profile = res_profile.scalar_one_or_none()
        if not profile:
            profile = ClientMemoryProfile(
                user_id=coachee.id,
                executive_summary="Marcus is a highly analytical VP of Engineering navigating rapid team expansion and board expectations. Focuses on delegation and cross-functional executive alignment.",
                leadership_style_and_patterns={
                    "archetype": "Architect / Visionary",
                    "core_strengths": ["Systems thinking", "Technical rigor", "Mission clarity"],
                    "growth_edges": ["Premature tactical intervention", "Direct debate with non-technical peers"],
                },
                stakeholder_map={
                    "CEO (Elena)": "High trust, demands clear product velocity metrics",
                    "VP Product (David)": "Occasional friction on scope vs engineering debt",
                    "Lead Directors": "Empowered, but Marcus sometimes over-reviews technical specs",
                },
                coach_private_notes="Responds exceptionally well to non-directive Socratic inquiry regarding his own energy expenditure when jumping into team execution.",
                version=1,
            )
            session.add(profile)
            print("  ✅ Created 360° Client Memory Profile for Marcus Vance")

        # 5. Create Active Client Goal
        res_goal = await session.execute(
            select(ClientGoal).where(ClientGoal.user_id == coachee.id).limit(1)
        )
        goal = res_goal.scalar_one_or_none()
        if not goal:
            goal = ClientGoal(
                user_id=coachee.id,
                title="Delegate Architecture Decision Record (ADR) sign-offs to Staff Engineers",
                description="Transition from directly reviewing all technical specs to establishing clear guardrails so Staff Engineers have full autonomy.",
                status="in_progress",
                readiness_stage="ready",
                source_type="coach_session",
                evidence_log=[
                    {
                        "date": datetime.now(timezone.utc).isoformat(),
                        "note": "Coaching session: Marcus agreed to shadow two ADR reviews and step back thereafter.",
                    }
                ],
            )
            session.add(goal)
            print("  ✅ Created Active Client Goal for Marcus Vance")

        # 6. Create Demo Conversation with Messages and Telemetry
        res_conv = await session.execute(
            select(Conversation).where(Conversation.user_id == coachee.id).limit(1)
        )
        conv = res_conv.scalar_one_or_none()
        if not conv:
            conv = Conversation(
                user_id=coachee.id,
                title="Delegation Boundaries with Staff Engineers",
            )
            session.add(conv)
            await session.flush()

            # Message 1 (User)
            m1 = Message(
                conversation_id=conv.id,
                role="user",
                content="I find myself spending 15 hours a week reviewing every single architecture proposal because I worry the team will make poor scaling choices.",
            )
            session.add(m1)

            # Message 2 (Assistant with Socratic Diagnostics & Telemetry)
            m2 = Message(
                conversation_id=conv.id,
                role="assistant",
                content="When you consider those 15 hours, what higher-leverage leadership responsibilities are currently being deprioritized or postponed as a consequence?",
                turn_diagnostics={
                    "socratic_stage": "Reality",
                    "cycle3_shift": "Opportunity Cost Awareness",
                    "cycle4_readiness": "ready",
                    "action_context": "Staff Engineer Autonomy & Architecture Reviews",
                    "rag_sources": [
                        {"source": "Dossier: Delegation Patterns", "similarity": 0.88}
                    ],
                    "guardrails": {"passed": True, "flags": []},
                    "telemetry": {
                        "trace_id": uuid.uuid4().hex,
                        "traceparent": f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01",
                        "ttft_ms": 342,
                        "context_retrieval_ms": 48,
                        "socratic_guard_ms": 19,
                        "generation_stream_ms": 1180,
                        "rag_degraded": False,
                        "usage": {
                            "prompt_tokens": 820,
                            "completion_tokens": 42,
                            "total_tokens": 862,
                            "model_name": "gpt-4o",
                            "cost_usd": 0.002470,
                        },
                    },
                },
            )
            session.add(m2)
            print("  ✅ Created Sample Socratic Conversation & Turn Telemetry")

        await session.commit()

    print("\n" + "=" * 60)
    print("🎉 DEMO DATA SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print("Demo Credentials:")
    print("  • Manager (Platform Owner): manager@company.com / Password123!")
    print("    URL: http://localhost:3000/dashboard/manager")
    print("  • Coach (Admin):           coach@company.com   / Password123!")
    print("    URL: http://localhost:3000/dashboard/users")
    print("  • Coachee (Executive):      coachee@company.com / Password123!")
    print("    URL: http://localhost:3000/coaching/new")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_data())

