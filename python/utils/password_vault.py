import os


class PasswordVault:
    @classmethod
    def get(cls):
        return os.environ["SUPERHUB_PASSWORD"]
