# Django Issue Tracker - UI Examples

This directory contains self-contained HTML files showcasing every state of the Django issue tracker application's UI. These files can be used to gather user feedback on the application's design and functionality.

## Generated Files

### Structure
- `state_descriptions.json` - Comprehensive mapping of all UI states and their requirements
- `templates/` - HTML files organized by template and state
- Template rendering scripts for regenerating files if needed

### Templates and States

#### Issue List (`templates/issues/issue_list.html/`)
- `authenticated_with_issues.html` - Logged-in user viewing multiple issues
- `unauthenticated_with_issues.html` - Anonymous user viewing issues
- `no_issues_authenticated.html` - Logged-in user with empty issue list
- `no_issues_unauthenticated.html` - Anonymous user with empty issue list
- `search_results.html` - Filtered results from search query
- `tag_filtered.html` - Issues filtered by selected tags
- `search_and_tag_filtered.html` - Combined search and tag filtering
- `no_tags_available.html` - Issue list when no tags exist

#### Issue Detail (`templates/issues/issue_detail.html/`)
- `normal_issue_with_comments.html` - Complete issue view with comments and history
- `normal_issue_no_comments.html` - Issue without any comments
- `deleted_issue.html` - Soft-deleted issue with restoration option
- `issue_not_author.html` - Issue viewed by non-author (limited actions)
- `unauthenticated_view.html` - Issue viewed by anonymous user
- `issue_no_description.html` - Issue with only summary, no description
- `issue_no_assignee_no_tags.html` - Minimal issue without assignee or tags

#### Issue Form (`templates/issues/issue_form.html/`)
- `create_issue.html` - New issue creation form
- `edit_issue.html` - Editing existing issue
- `form_with_errors.html` - Form with validation errors

#### Settings (`templates/issues/settings.html/`)
- `settings_form.html` - Configuration form for Slack and GitHub integrations
- `settings_form_with_errors.html` - Settings form with validation errors

#### Tag Management (`templates/issues/tag_list.html/`, `templates/issues/tag_form.html/`)
- `tags_available.html` - List of existing tags with usage counts
- `no_tags.html` - Empty tag list
- `create_tag.html` - New tag creation form
- `edit_tag.html` - Tag editing form
- `form_with_errors.html` - Tag form with validation errors

#### Authentication (`templates/registration/`)
- `login_form.html` - Email-based login form
- `login_form_with_errors.html` - Login form with error messages
- `register_form.html` - User registration form
- `register_form_with_errors.html` - Registration form with validation errors

## Features Demonstrated

### User Authentication States
- Authenticated vs unauthenticated user experiences
- Different permissions (author vs non-author, staff vs regular user)
- Registration and login flows

### Issue Management
- Full CRUD operations for issues
- Soft delete functionality with restoration
- Issue assignment and status management
- Tag categorization system

### UI Components
- Responsive design with Tailwind CSS
- Form validation and error handling
- Search and filtering functionality
- Comment system with inline editing
- Edit history tracking

### Integrations
- Slack notification configuration
- GitHub repository monitoring setup

## Usage

These HTML files are fully self-contained and can be:
1. Opened directly in web browsers for review
2. Shared with stakeholders for feedback
3. Used for design reviews and user testing
4. Referenced for UI/UX documentation

Each file represents a specific user journey or interaction state, allowing for comprehensive coverage of the application's functionality.

## Regeneration

To regenerate these files after template changes:
1. Update the corresponding JSON files in the template directories
2. Run `python simple_renderer.py` from the project root
3. All HTML files will be regenerated with the updated template content

## Technical Notes

- All Django template tags have been processed and replaced with static content
- URLs are converted to placeholder paths
- Form fields include proper validation states
- Responsive design elements are preserved
- JavaScript functionality is included for interactive elements