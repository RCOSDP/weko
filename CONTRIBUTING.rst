Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/wekosoftware/weko/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

WEKO could always use more documentation, whether as part of the
official WEKO docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/wekosoftware/weko/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `weko` for local development.

1. Fork the `wekosoftware/weko` repo on GitHub.
2. Clone your fork locally:

   .. code-block:: console

      $ git clone git@github.com:your_name_here/weko.git

3. Set up the local development environment with Docker. The current
   repository workflow uses ``install.sh`` to build containers, initialize
   services, and populate the instance:

   .. code-block:: console

      $ cd weko/
      $ ./install.sh

4. Create a branch for local development:

   .. code-block:: console

      $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass tests:

   .. code-block:: console

      $ ./run-tests.sh

   For targeted module work, you can also use the module-level commands
   documented in ``README-TEST.md``.

6. Commit your changes and push your branch to GitHub:

   .. code-block:: console

      $ git add .
      $ git commit -s
          -m "component: title without verbs"
          -m "* NEW Adds your new feature."
          -m "* FIX Fixes an existing issue."
          -m "* BETTER Improves and existing feature."
          -m "* Changes something that should not be visible in release notes."
      $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests and must not decrease test coverage.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should work for Python 2.7, 3.5 and 3.6. Check
   https://travis-ci.org/wekosoftware/weko/pull_requests
   and make sure that the tests pass for all supported Python versions.

AI-Assisted Development Workflow
--------------------------------

When using coding agents such as Codex, Claude Code, Gemini CLI, or GitHub
Copilot, follow a
single shared workflow so repository knowledge accumulates instead of being
rediscovered in each session.

1. Treat ``AGENTS.md`` as the canonical agent instruction file.
2. Before starting work, read ``AGENTS.md`` and then the project-root files
   ``task_plan.md``, ``findings.md``, and ``progress.md``.
3. Do not repeat full-repository exploration on every task. Read only the
   target module and the files needed for the current change.
4. Append reusable discoveries to ``findings.md``.
5. Record actions taken, tests run, and failures encountered in
   ``progress.md``.
6. For multi-step work, add or update phases in ``task_plan.md``.
7. Keep ``AGENTS.md`` short and durable. Store temporary investigation notes in
   ``findings.md`` and ``progress.md`` instead of expanding ``AGENTS.md``.

Pull requests should state:

* Which persistent context files were reviewed.
* Which persistent context files were updated.
* What tests were run.
* Any known gaps, assumptions, or follow-up work.
