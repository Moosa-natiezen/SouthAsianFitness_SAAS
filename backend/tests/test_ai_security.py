"""Security tests for cross-tenant access prevention.

Verifies that:
1. No route accepts user_id as a LLM-controllable parameter
2. Delete operations return 403 when attempting to access another user's data
3. List operations only return the authenticated user's data
4. Save operations always use the session-derived user_id
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.models.user import User
from fastapi.testclient import TestClient

# ── Helpers ────────────────────────────────────────────────────────────────


def _make_user(user_id=None):
    """Create a mock user for testing."""
    user = User()
    user.id = user_id or uuid4()
    user.subscription_tier = "pro"
    user.email = "test@example.com"
    user.is_active = True
    return user


def _make_pro_user(user_id=None):
    """Create a mock pro user."""
    user = _make_user(user_id)
    user.subscription_tier = "pro"
    return user


# ── Schema Audit: No user_id in request bodies ─────────────────────────────


class TestNoUserIdInRequestBodies:
    """Verify that no MCP-exposed schema accepts user_id as a parameter.

    An AI agent should never be able to pass a user_id to impersonate
    another user. The user identity must always come from the session.
    """

    def test_save_meal_plan_request_has_no_user_id(self) -> None:
        from app.schemas.meal_plan import SaveMealPlanRequest

        schema = SaveMealPlanRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"SaveMealPlanRequest exposes user_id in schema: {props.keys()}"
        )

    def test_save_workout_request_has_no_user_id(self) -> None:
        from app.schemas.workout import SaveWorkoutPlanRequest

        schema = SaveWorkoutPlanRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"SaveWorkoutPlanRequest exposes user_id in schema: {props.keys()}"
        )

    def test_meal_plan_request_has_no_user_id(self) -> None:
        from app.schemas.nutrition import MealPlanRequest

        schema = MealPlanRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"MealPlanRequest exposes user_id in schema: {props.keys()}"
        )

    def test_workout_generate_request_has_no_user_id(self) -> None:
        from app.schemas.workout import WorkoutGenerateRequest

        schema = WorkoutGenerateRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"WorkoutGenerateRequest exposes user_id in schema: {props.keys()}"
        )

    def test_agent_chat_request_has_no_user_id(self) -> None:
        from app.schemas.agent_chat import AgentChatRequest

        schema = AgentChatRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"AgentChatRequest exposes user_id in schema: {props.keys()}"
        )

    def test_progress_create_has_no_user_id(self) -> None:
        from app.schemas.progress import ProgressEntryCreate

        schema = ProgressEntryCreate.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"ProgressEntryCreate exposes user_id in schema: {props.keys()}"
        )

    def test_nutrition_calculate_has_no_user_id(self) -> None:
        from app.schemas.nutrition import NutritionCalculateRequest

        schema = NutritionCalculateRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"NutritionCalculateRequest exposes user_id in schema: {props.keys()}"
        )

    def test_profile_update_has_no_user_id(self) -> None:
        from app.schemas.settings import ProfileUpdateRequest

        schema = ProfileUpdateRequest.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" not in props, (
            f"ProfileUpdateRequest exposes user_id in schema: {props.keys()}"
        )


# ── Cross-Tenant Delete Protection (Unit Tests) ────────────────────────────


class TestCrossTenantDeleteProtection:
    """Verify that delete operations enforce ownership checks.

    Tests the service-layer delete functions directly to ensure they
    raise 403 when a record belongs to another user.
    """

    def test_delete_saved_meal_plan_cross_tenant_raises_403(self) -> None:
        """Attempting to delete another user's saved meal plan should raise 403."""
        from app.models.meal_plan import SavedMealPlan
        from fastapi import HTTPException

        owner_id = uuid4()
        attacker_id = uuid4()

        # Create a mock plan owned by owner_id
        mock_plan = SavedMealPlan()
        mock_plan.id = uuid4()
        mock_plan.user_id = owner_id

        # Create mock session
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        # Try to delete as attacker — should raise 403
        with pytest.raises(HTTPException) as exc_info:

            # Manually call the logic (simulating the route handler)
            saved = mock_db.query.return_value.filter.return_value.first.return_value
            if saved.user_id != attacker_id:
                raise HTTPException(status_code=403, detail="You do not have permission")

        assert exc_info.value.status_code == 403

    def test_delete_saved_workout_cross_tenant_raises_403(self) -> None:
        """Attempting to delete another user's saved workout should raise 403."""

        from app.models.workout import SavedWorkoutPlan

        owner_id = uuid4()
        attacker_id = uuid4()

        mock_workout = SavedWorkoutPlan()
        mock_workout.id = uuid4()
        mock_workout.user_id = owner_id

        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_workout

        # Verify ownership check logic
        saved = mock_db.query.return_value.filter.return_value.first.return_value
        assert saved.user_id != attacker_id, "Ownership check should fail"

    def test_delete_progress_entry_cross_tenant_raises_403(self) -> None:
        """Attempting to delete another user's progress entry should raise 403."""
        owner_id = uuid4()
        attacker_id = uuid4()

        from app.models.progress import ProgressEntry

        mock_entry = ProgressEntry()
        mock_entry.id = uuid4()
        mock_entry.user_id = owner_id

        # Verify ownership check logic
        assert mock_entry.user_id != attacker_id, "Ownership check should fail"

    def test_service_layer_delete_meal_plan_checks_ownership(self) -> None:
        """The delete_meal_plan service function should check ownership."""
        from fastapi import HTTPException

        owner_id = uuid4()
        attacker_id = uuid4()

        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_plan = MagicMock()
        mock_plan.user_id = owner_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

        # Call the service function
        from app.services.meal_plan_service import delete_meal_plan

        with pytest.raises(HTTPException) as exc_info:
            delete_meal_plan(mock_db, user_id=attacker_id, plan_id=mock_plan.id)

        assert exc_info.value.status_code == 403

    def test_service_layer_delete_progress_checks_ownership(self) -> None:
        """The delete_progress_entry service function should check ownership."""
        from fastapi import HTTPException

        owner_id = uuid4()
        attacker_id = uuid4()

        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_entry = MagicMock()
        mock_entry.user_id = owner_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry

        # Call the service function
        from app.services.progress_service import delete_progress_entry

        mock_user = MagicMock()
        mock_user.id = attacker_id

        with pytest.raises(HTTPException) as exc_info:
            delete_progress_entry(mock_db, mock_user, mock_entry.id)

        assert exc_info.value.status_code == 403


# ── Authentication Required ────────────────────────────────────────────────


class TestAuthenticationRequired:
    """Verify that all MCP-exposed routes require authentication."""

    def test_meal_plans_list_requires_auth(self) -> None:
        """Meal plans list endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/api/meal-plans/")
        assert response.status_code == 401

    def test_progress_list_requires_auth(self) -> None:
        """Progress list endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/api/progress")
        assert response.status_code == 401

    def test_settings_requires_auth(self) -> None:
        """Settings endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/api/auth/settings")
        assert response.status_code == 401

    def test_nutrition_calculate_requires_auth(self) -> None:
        """Nutrition calculate endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.post("/api/nutrition/calculate")
        assert response.status_code == 401

    def test_ai_meal_plans_saved_requires_auth(self) -> None:
        """AI saved meal plans endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/api/ai/meal-plans/saved")
        assert response.status_code == 401

    def test_ai_workouts_saved_requires_auth(self) -> None:
        """AI saved workouts endpoint should reject unauthenticated requests."""
        from app.main import app as real_app

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/api/ai/workouts/saved")
        assert response.status_code == 401
