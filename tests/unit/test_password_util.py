from util.password_util import PasswordUtil


def test_password_hash_can_be_verified_without_storing_plaintext():
    password_hash = PasswordUtil.hash_password("secret1")

    assert password_hash != "secret1"
    assert password_hash.startswith("$argon2id$")
    assert PasswordUtil.verify_password("secret1", password_hash)
    assert not PasswordUtil.verify_password("wrong-password", password_hash)


def test_invalid_password_hash_is_rejected():
    assert not PasswordUtil.verify_password("secret1", "not-an-argon2-hash")
