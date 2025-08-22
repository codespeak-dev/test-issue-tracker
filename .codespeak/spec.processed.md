Bugger is an issue tracking application.

# Technology

- Django
- Tailwind CSS

# Issues

- Issues
    - id
    - summary (one line)
    - description (mardown)
    - status
    - author
    - created_at
    - updated_at
    - assignee
    - comments
    - tags

- Statuses
    - name
    - open/closed

Predifined statuses:
    - Open (open)
    - In Progress (open)
    - Done (closed)
    - Rejected (closed)

- Comments
    - content (markdown)
    - author
    - created_at
    - updated_at

 - Tags
     - name
     - color

# Users and authentication

When a user is not logged in, the issues are read-only for them. 
Anyone can register on the Sign up page (provide name and email, no password needed).

If the user is not logged in, they see a "Log in" button in the top right corner.
If the user is logged in, they see a "Log out" button in the top right corner next to their name.

# User stories

## User not logged in

- Log in (ask for email, no password needed)
  - if no registered, sign up
- See list of issues
  - summary, status, author, updated_at
 - filter by free-form text (match with summary and description)
- Open issue
  - see all the details and comments

## User logged in

- Create new issue
  - default status is Open
- Delete issue
  - Restore deteled issue
- Add comment
- Edit issue
  - not editable: author, created_at, updated_at
  - anyone can edit an issue, but the history of who edited and when is preserved
- Edit comment
- Add tag
- Edit tag
- Remove tag
- Filter by tag

# Integrations

## Slack

- Configured in Settings
- When a new issue is created, a message is posted to the channel
  - when a comment is added, a message is posted to the thread started by the issue creation notification

## Github

We don't use Github webhooks. We poll the Github API every 10 seconds for new commits.

- Configured in Settings
- When a commit is merged with `#<issue-id> Fixed` in the commit message, the issue is closed and a comment is added to the issue with the commit message and a link to the commit