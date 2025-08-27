# UI Examples for Bugger Issue Tracker

This directory contains generated HTML files representing every state of the Django issue tracker application's UI. These files are self-contained and can be opened in any web browser to preview the different application states.

## Structure

Each template has multiple states showing different data conditions and user interactions:

### Base Template (`templates/base.html/`)
- `authenticated_user.html` - Base layout with logged-in user
- `unauthenticated.html` - Base layout for anonymous users  
- `with_success_messages.html` - Base layout showing success messages
- `with_error_messages.html` - Base layout showing error messages

### Issue List (`templates/issues/issue_list.html/`)
- `empty_list_authenticated.html` - No issues, logged-in user
- `empty_list_unauthenticated.html` - No issues, anonymous user
- `populated_list_with_tags.html` - Multiple issues with tags and different statuses
- `search_results.html` - Search results for "bug" query
- `filtered_by_tags.html` - Issues filtered by "Bug" tag

### Issue Detail (`templates/issues/issue_detail.html/`)
- `normal_issue.html` - Complete issue with comments, tags, assignee, and edit history
- `deleted_issue.html` - Soft-deleted issue with restore option
- `issue_no_comments.html` - Issue without any comments
- `issue_unauthenticated.html` - Issue viewed by anonymous user (no comment form)

### Issue Form (`templates/issues/issue_form.html/`)
- `create_form.html` - New issue creation form
- `edit_form.html` - Issue editing form with existing data
- `form_with_errors.html` - Form with validation errors (red borders, error messages)

### Login/Registration (`templates/registration/`)
- `login.html/empty_form.html` - Clean login form
- `login.html/form_with_errors.html` - Login form with "user not found" error
- `register.html/empty_form.html` - Clean registration form  
- `register.html/form_with_errors.html` - Registration form with validation errors

### Settings (`templates/issues/settings.html/`)
- `empty_settings.html` - Settings form with no integrations configured
- `populated_settings.html` - Settings form with Slack and GitHub integration data

### Tag Management (`templates/issues/tag_list.html/` & `tag_form.html/`)
- `tag_list.html/empty_tags.html` - No tags created yet
- `tag_list.html/populated_tags.html` - Multiple tags with different colors and usage counts
- `tag_form.html/create_tag.html` - Create new tag form
- `tag_form.html/edit_tag.html` - Edit existing tag form with color preview

## Features Demonstrated

### Navigation & Authentication
- Different navigation items for authenticated vs anonymous users
- Staff-only settings access
- User greeting with actual names

### Forms & Validation
- Proper HTML form elements (input, textarea, select, checkbox)
- Error states with red borders and error messages
- Form field labels with correct `for` attributes
- CSRF token inclusion

### Data Display
- Issue lists with proper sorting by update date
- Tag filtering with colored labels
- Status badges (open/closed) with appropriate styling
- Comments with markdown rendering
- Edit history tracking

### Interactive Elements
- Search functionality with query persistence
- Tag filtering checkboxes that auto-submit
- Delete/restore buttons for issue authors
- Comment editing modal (JavaScript included)

### Responsive Design
- Tailwind CSS styling throughout
- Mobile-friendly responsive classes
- Proper grid layouts for forms

## Usage

Open any HTML file in a web browser to see how the application would look in that particular state. These files are useful for:

- Design reviews and feedback collection
- Frontend development reference
- Documentation of application states
- User experience testing

All files are self-contained with embedded CSS (via Tailwind CDN) and JavaScript functionality preserved.