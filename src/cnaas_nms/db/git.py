import enum

from git import Repo
from git import InvalidGitRepositoryError, NoSuchPathError
from git.exc import NoSuchPathError
import yaml

from cnaas_nms.db.exceptions import ConfigException
from cnaas_nms.tools.log import get_logger
from cnaas_nms.db.settings import get_settings, SettingsSyntaxError

logger = get_logger()


class RepoType(enum.Enum):
    TEMPLATES = 0
    SETTINGS = 1

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_name(cls, value):
        return any(value == item.name for item in cls)


def get_repo_status(repo_type: RepoType = RepoType.TEMPLATES) -> str:
    with open('/etc/cnaas-nms/repository.yml', 'r') as db_file:
        repo_config = yaml.safe_load(db_file)

    if repo_type == RepoType.TEMPLATES:
        local_repo_path = repo_config['templates_local']
        remote_repo_path = repo_config['templates_remote']
    elif repo_type == RepoType.SETTINGS:
        local_repo_path = repo_config['settings_local']
        remote_repo_path = repo_config['settings_remote']
    else:
        raise ValueError("Invalid repository")

    try:
        local_repo = Repo(local_repo_path)
        return 'Commit {} by {} at {}\n'.format(
            local_repo.head.commit.name_rev,
            local_repo.head.commit.committer,
            local_repo.head.commit.committed_datetime
        )
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        return 'Repository is not yet cloned from remote'


def refresh_repo(repo_type: RepoType = RepoType.TEMPLATES) -> str:
    """Refresh the repository for repo_type

    Args:
        repo_type: Which repository to refresh

    Returns:
        String describing what was updated.

    Raises:
        cnaas_nms.db.settings.SettingsSyntaxError
    """

    with open('/etc/cnaas-nms/repository.yml', 'r') as db_file:
        repo_config = yaml.safe_load(db_file)

    if repo_type == RepoType.TEMPLATES:
        local_repo_path = repo_config['templates_local']
        remote_repo_path = repo_config['templates_remote']
    elif repo_type == RepoType.SETTINGS:
        local_repo_path = repo_config['settings_local']
        remote_repo_path = repo_config['settings_remote']
    else:
        raise ValueError("Invalid repository")

    ret = ''
    try:
        local_repo = Repo(local_repo_path)
        diff = local_repo.remotes.origin.pull()
        for item in diff:
            ret += 'Commit {} by {} at {}\n'.format(
                item.commit.name_rev,
                item.commit.committer,
                item.commit.committed_datetime
            )
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        logger.info("Local repository {} not found, cloning from remote".\
                    format(local_repo_path))
        try:
            remote_repo = Repo(remote_repo_path)
        except NoSuchPathError as e:
            raise ConfigException("Invalid remote repository {}: {}".format(
                remote_repo_path,
                str(e)
            ))

        remote_repo.clone(local_repo_path)
        local_repo = Repo(local_repo_path)
        ret = 'Cloned new from remote. Last commit {} by {} at {}'.format(
            local_repo.head.commit.name_rev,
            local_repo.head.commit.committer,
            local_repo.head.commit.committed_datetime
        )

    if repo_type == RepoType.SETTINGS:
        try:
            get_settings()
        except SettingsSyntaxError as e:
            raise e


    # TODO: Also return what devices were affected so we can change the to unsync?

    return ret

