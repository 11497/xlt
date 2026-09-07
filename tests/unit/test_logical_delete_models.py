import pytest
from pydantic import ValidationError

from model.document_model import Document
from model.knowledge_base_model import KnowledgeBase
from model.role_model import Role
from model.user_model import User, UserRegistration
from util.soft_delete_name import tombstone_unique_name


@pytest.mark.parametrize("model, data", [
    (KnowledgeBase, {"name": "测试库", "is_deleted": 1}),
    (Document, {
        "knowledge_base_id": 1,
        "filename": "a.txt",
        "storage_path": "knowledge_base/1/a.txt",
        "create_time": "2026-01-01T00:00:00",
        "update_time": "2026-01-01T00:00:00",
        "deleted_at": "2026-01-01T00:00:00",
    }),
])
def test_request_models_reject_internal_soft_delete_fields(model, data):
    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_database_row_factory_can_retain_internal_fields():
    model = KnowledgeBase.from_row({"id": 1, "name": "测试库", "is_deleted": 1})
    assert model.is_deleted == 1
    assert model.model_dump(exclude_none=False).get("is_deleted") is None


def test_tombstone_name_cannot_be_submitted_as_create_param():
    original = "a" * 15
    tombstone = tombstone_unique_name(original)
    assert len(tombstone) > 15
    with pytest.raises(ValidationError):
        User(username=tombstone, password="123456")
    with pytest.raises(ValidationError):
        UserRegistration(username=tombstone, password="123456")
    with pytest.raises(ValidationError):
        Role(name=tombstone)
    with pytest.raises(ValidationError):
        KnowledgeBase(name=tombstone)


def test_from_row_accepts_tombstone_name_without_length_validation():
    tombstone = tombstone_unique_name("alice")
    user = User.from_row({"id": 1, "username": tombstone, "password": "hashed", "is_deleted": 1})
    role = Role.from_row({"id": 1, "name": tombstone, "is_deleted": 1})
    knowledge_base = KnowledgeBase.from_row({"id": 1, "name": tombstone, "is_deleted": 1})
    assert user.username == tombstone
    assert role.name == tombstone
    assert knowledge_base.name == tombstone

