(function() {
    'use strict';
    
    let isEditMode = false;
    let editIcon = null;
    let currentHighlighted = null;
    
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
            editIcon.style.background = '#007bff';
            editIcon.style.color = '#fff';
            document.addEventListener('mousemove', highlightElement);
            document.addEventListener('mouseleave', clearHighlight);
        } else {
            editIcon.style.background = '#fff';
            editIcon.style.color = '#333';
            document.removeEventListener('mousemove', highlightElement);
            document.removeEventListener('mouseleave', clearHighlight);
            clearHighlight();
        }
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
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createEditIcon);
    } else {
        createEditIcon();
    }
})();