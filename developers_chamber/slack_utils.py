import re

from slack_sdk import WebClient

from developers_chamber.qa.base import RepoMixin


class RecentMigrationsSlackUploader(RepoMixin):

    def __init__(self, token, channel, target_branch, migrations_pattern):
        self.client = WebClient(token=token)
        self.channel = channel
        self.target_branch = target_branch
        self.migrations_pattern = r'{}'.format(migrations_pattern)
        self.active_branch = self._get_active_branch_name()
        self.repo = self._get_repo()

    def _get_migration_files(self):
        return [diff.b_path for diff in self.repo.commit(self.target_branch).diff(self.active_branch, create_patch=True)
                if diff.new_file and re.search(self.migrations_pattern, diff.b_path)]

    def send_message(self, msg):
        self.client.chat_postMessage(channel=self.channel, text=msg)

    def upload_file(self, file):
        self.client.files_upload(channels=self.channel, file=file, title=file)

    def run(self):
        migration_files = self._get_migration_files()
        if migration_files:
            self.send_message(
                f'Uploading *new migration files* ({len(migration_files)}) between'
                f' `{self.active_branch}` and `{self.target_branch}` git branches :arrow_down:'
            )
            for file in migration_files:
                self.upload_file(file=file)
            self.send_message('Done :white_check_mark:')
        else:
            self.send_message((
                'Cannot find any *new migrations files* between'
                f' `{self.active_branch}` and `{self.target_branch}` git branches :travolta:'
            ))


def upload_new_migration(token, channel, target_branch, migrations_pattern):
    RecentMigrationsSlackUploader(token, channel, target_branch, migrations_pattern).run()
