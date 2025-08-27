(function() {
    'use strict';
    
    let isEditMode = false;
    let editIcon = null;
    let currentHighlighted = null;
    let currentEditing = null;
    
    function createEditIcon() {
        editIcon = document.createElement('div');
        editIcon.innerHTML = '✏️';
        editIcon.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: #fff;
            border: 2px solid #333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10000;
            font-size: 18px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            user-select: none;
        `;
        
        editIcon.addEventListener('click', toggleEditMode);
        document.body.appendChild(editIcon);
    }
    
    function toggleEditMode() {
        isEditMode = !isEditMode;
        
        if (isEditMode) {
            editIcon.innerHTML = '💾';
            editIcon.style.background = '#007bff';
            editIcon.style.color = '#fff';
            document.addEventListener('mousemove', highlightElement);
            document.addEventListener('mouseleave', clearHighlight);
            document.addEventListener('click', handleElementClick);
            window.addEventListener('beforeunload', handleBeforeUnload);
        } else {
            // Save mode - send the HTML to server
            saveChanges();
        }
    }
    
    function saveChanges() {
        // Show saving message
        editIcon.innerHTML = '⏳';
        editIcon.style.background = '#ffc107';
        
        // Get current page HTML
        const html = document.documentElement.outerHTML;
        
        // Send to server
        fetch('/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                html: html,
                path: window.location.pathname
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload the page with updated template
                window.location.reload();
            } else {
                alert(`Save failed: ${data.error}`);
                // Reset to edit mode
                editIcon.innerHTML = '💾';
                editIcon.style.background = '#007bff';
            }
        })
        .catch(error => {
            console.error('Save error:', error);
            alert('Save failed: Network error');
            // Reset to edit mode
            editIcon.innerHTML = '💾';
            editIcon.style.background = '#007bff';
        });
    }
    
    function exitEditMode() {
        editIcon.innerHTML = '✏️';
        editIcon.style.background = '#fff';
        editIcon.style.color = '#333';
        document.removeEventListener('mousemove', highlightElement);
        document.removeEventListener('mouseleave', clearHighlight);
        document.removeEventListener('click', handleElementClick);
        window.removeEventListener('beforeunload', handleBeforeUnload);
        clearHighlight();
        stopEditing();
        isEditMode = false;
    }
    
    function highlightElement(e) {
        if (!isEditMode) return;
        
        const element = document.elementFromPoint(e.clientX, e.clientY);
        
        if (element && element !== editIcon && element !== currentHighlighted) {
            clearHighlight();
            currentHighlighted = element;
            currentHighlighted.style.outline = '3px solid #007bff';
            currentHighlighted.style.outlineOffset = '2px';
        }
    }
    
    function clearHighlight() {
        if (currentHighlighted) {
            currentHighlighted.style.outline = '';
            currentHighlighted.style.outlineOffset = '';
            currentHighlighted = null;
        }
    }
    
    function handleElementClick(e) {
        if (!isEditMode || !currentHighlighted) return;
        if (e.target === editIcon) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        startEditing(currentHighlighted);
    }
    
    function startEditing(element) {
        stopEditing();
        
        currentEditing = element;
        element.contentEditable = true;
        element.style.outline = '3px solid #007bff';
        element.style.outlineOffset = '2px';
        element.focus();
        
        element.addEventListener('blur', handleEditFinish);
        element.addEventListener('keydown', handleEditKeydown);
    }
    
    function stopEditing() {
        if (currentEditing) {
            currentEditing.contentEditable = false;
            currentEditing.style.outline = '';
            currentEditing.style.outlineOffset = '';
            currentEditing.removeEventListener('blur', handleEditFinish);
            currentEditing.removeEventListener('keydown', handleEditKeydown);
            currentEditing = null;
        }
    }
    
    function handleEditFinish() {
        stopEditing();
    }
    
    function handleEditKeydown(e) {
        if (e.key === 'Escape') {
            stopEditing();
        } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            stopEditing();
        }
    }
    
    function handleBeforeUnload(e) {
        if (isEditMode) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createEditIcon);
    } else {
        createEditIcon();
    }
})();