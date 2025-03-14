import pytest
from inginious.frontend.models.user import User


@pytest.mark.asyncio(loop_scope="module")
class TestUserModel:
    async def test_create_valid_user_basic(self, test_db):
        """
        Test creating a valid user.
        """
        user = User(
            username="j-d_o~e|",
            realname="John Doe",
            email="john@doe.com",
            password="password"
        )

        await user.insert()
        fetched_user = await User.find_one(User.username == "j-d_o~e|")

        assert fetched_user is not None
        assert fetched_user.username == "j-d_o~e|"
        assert fetched_user.realname == "John Doe"
        assert fetched_user.email == "john@doe.com"
        assert fetched_user.password == "password"
        assert fetched_user.bindings == {}
        assert fetched_user.language == "en"
        assert fetched_user.activate is None
        assert fetched_user.reset is None
        assert fetched_user.api_key is None
        assert fetched_user.tos_accepted == False


    async def test_username_validation(self, test_db):
        """
        Test username validation.
        """
        with pytest.raises(ValueError, match="Invalid username format"):
            User(username="A", realname="John Doe", email="john@doe.com", password="password")

        with pytest.raises(ValueError, match="Invalid username format"):
            User(username="john@doe", realname="John Doe", email="john@doe.com", password="password")

        with pytest.raises(ValueError, match="Invalid username format"):
            User(username="jdoe!", realname="John Doe", email="john@doe.com", password="password")

        with pytest.raises(ValueError, match="Invalid username format"):
            User(username="j#doe", realname="John Doe", email="john@doe.com", password="password")

    async def test_email_sanitization(self, test_db):
        """
        Test email sanitization.
        """
        user = User(username="jdoe", realname="John Doe", email="John@Doe.COM", password="password")

        assert user.email == "John@doe.com"


    async def test_wrong_email(self, test_db):
        """
        Test username validation.
        """
        with pytest.raises(ValueError, match="Invalid email format."):
            User(username="jdoe", realname="John Doe", email="johndoe.com", password="password")

        with pytest.raises(ValueError, match="Invalid email format."):
            User(username="jdoe", realname="John Doe", email="john@doecom", password="password")

        with pytest.raises(ValueError, match="Invalid email format."):
            User(username="jdoe", realname="John Doe", email="john@john@doe.com", password="password")

        with pytest.raises(ValueError, match="Invalid email format."):
            User(username="jdoe", realname="John Doe", email="johndoecom", password="password")
