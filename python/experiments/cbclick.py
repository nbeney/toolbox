from __future__ import print_function

from click import *


def _patch_click():
    import click

    def hyphenate_group_commands():
        # TODO: Stop copying code from click, wrap it!
        def command(self, *args, **kwargs):
            def decorator(f):
                if 'name' in kwargs:
                    cmd = click.command(*args, **kwargs)(f)
                else:
                    name = f.__name__.replace('_', '-')
                    cmd = click.command(*args, name=name, **kwargs)(f)
                self.add_command(cmd)
                return cmd

            return decorator

        click.Group.command = command

    hyphenate_group_commands()


_patch_click()
