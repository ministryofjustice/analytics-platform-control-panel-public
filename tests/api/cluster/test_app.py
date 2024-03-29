# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# First-party/Local
from controlpanel.api import cluster, models
from controlpanel.api.cluster import BASE_ASSUME_ROLE_POLICY


@pytest.fixture
def app():
    return models.App(slug="slug", repo_url="https://gitpub.example.com/test-repo")


@pytest.fixture
def aws_create_role():
    with patch(
        "controlpanel.api.cluster.AWSRole.create_role"
    ) as aws_create_role_action:
        yield aws_create_role_action


@pytest.fixture
def aws_delete_role():
    with patch(
        "controlpanel.api.cluster.AWSRole.delete_role"
    ) as aws_delete_role_action:
        yield aws_delete_role_action


@pytest.fixture(autouse=True)
def githubapi():
    """
    Mock calls to Github
    """
    with patch("controlpanel.api.cluster.GithubAPI") as GithubAPI:
        yield GithubAPI.return_value


@pytest.fixture(autouse=True)
def repos(githubapi):
    test_repo = {
        "full_name": "Test App",
        "html_url": "https://github.com/moj-analytical-services/test_app",
    }
    githubapi.get_repository.return_value = test_repo
    githubapi.get_repo_envs.return_value = ["test"]
    yield githubapi


def test_app_create_iam_role(aws_create_role, app):
    cluster.App(app).create_iam_role()
    aws_create_role.assert_called_with(app.iam_role_name, BASE_ASSUME_ROLE_POLICY)


@pytest.fixture  # noqa: F405
def authz():
    with patch("controlpanel.api.auth0.ExtendedAuth0") as authz:
        yield authz()


def test_app_delete(aws_delete_role, app, authz):
    app.repo_url = "https://github.com/moj-analytical-services/my_repo"
    cluster.App(app, github_api_token="testing").delete()
    aws_delete_role.assert_called_with(app.iam_role_name)


@pytest.fixture
def ExtendedAuth0():
    with patch("controlpanel.api.auth0.ExtendedAuth0") as authz:
        authz.DEFAULT_CONNECTION_OPTION = "email"
        yield authz.return_value


def test_update_auth_connections(app, ExtendedAuth0):
    with patch.object(ExtendedAuth0, "get_client_enabled_connections") as get_conns, \
            patch.object(ExtendedAuth0, "update_client_auth_connections") as update_conns, \
            patch("controlpanel.api.cluster.App.create_or_update_env_var") as create_or_update:
        testing_env = "testing_env"
        testing_client_id = "testing_client_id"
        app.app_conf = {
            models.App.KEY_WORD_FOR_AUTH_SETTINGS: {
                testing_env: {"client_id": testing_client_id}
            }
        }
        app.repo_url = "https://github.com/moj-analytical-services/my_repo"

        # Change to use non-passwordless connection
        new_conns = {"github": {}},
        get_conns.return_value = {
            testing_client_id: "email"
        }
        cluster.App(app, github_api_token="testing").update_auth_connections(
            testing_env,
            new_conns=new_conns
        )
        create_or_update.assert_called_with(
            env_name='testing_env',
            key_name='AUTH0_PASSWORDLESS',
            key_value=False)
        update_conns.assert_called_with(
            app_name='data-platform-app-slug-testing_env',
            client_id='testing_client_id',
            new_conns=new_conns,
            existing_conns='email')

        # Change to use passwordless connection
        new_conns = {"email": {}}
        get_conns.return_value = {
            testing_client_id: "github"
        }
        cluster.App(app, github_api_token="testing").update_auth_connections(
            testing_env,
            new_conns=new_conns
        )
        create_or_update.assert_called_with(
            env_name='testing_env',
            key_name='AUTH0_PASSWORDLESS',
            key_value=True)
        update_conns.assert_called_with(
            app_name='data-platform-app-slug-testing_env',
            client_id='testing_client_id',
            new_conns=new_conns,
            existing_conns='github')


mock_ingress = MagicMock(name="Ingress")
mock_ingress.spec.rules = [MagicMock(name="Rule", host="test-app.example.com")]
