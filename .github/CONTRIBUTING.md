## Submitting an issue

Bug reports and feature requests can be submitted to the
[Issue Tracker](https://github.com/thebigmunch/google-music-scripts/issues).
For discussion and support, use the [Discourse forum](https://forum.thebigmunch.me).

Some general guidelines to follow:

* Use an appropriate, descriptive title.
* Provide as many details as possible.
* Don't piggy-back. Keep separate topics in separate issues.

## Submitting code

Patches are welcome.
Keep your code consistent with the rest of the project.
[PEP8](https://www.python.org/dev/peps/pep-0008/) is a good guide,
but with the following exceptions to keep in mind for coding/linting:

* Tabs should be used for indentation of code.
* Don't use line continuation that aligns with opening delimiter.
* Readability and understandibility are more important than arbitrary rules.

Some linter errors may need to be ignored to accommodate these differences.

### Pull Requests

[Pull Requests](https://help.github.com/articles/creating-a-pull-request) should originate from a
[feature branch][fb] in your [fork][fork], not from the **master** branch.

Commit messages should be written in a
[well-formed, consistent](https://sethrobertson.github.io/GitBestPractices/#usemsg) manner.
See the [commit log](https://github.com/thebigmunch/google-music-scripts/commits) for acceptable examples.

Each commit should encompass the smallest logical changeset.
E.g. changing two unrelated things in the same file would be two commits rather than one commit of "Change filename".

If you made a mistake in a commit in your Pull Request, you should
[amend or rebase](https://www.atlassian.com/git/tutorials/rewriting-history) to change your previous commit(s)
then [force push](http://stackoverflow.com/a/12610763) to the [feature branch][fb] in your [fork][fork].

[fb]: https://help.github.com/articles/creating-and-deleting-branches-within-your-repository/#creating-a-branch
[fork]: https://help.github.com/articles/fork-a-repo

## Misc
For anything else, contact the author by e-mail at <mail@thebigmunch.me>.
