(function() {
    'use strict';
    
    let isEditMode = false;
    let editIcon = null;
    let currentHighlighted = null;
    let currentEditor = null;
    
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
            document.addEventListener('click', handleElementClick);
        } else {
            editIcon.style.background = '#fff';
            editIcon.style.color = '#333';
            document.removeEventListener('mousemove', highlightElement);
            document.removeEventListener('mouseleave', clearHighlight);
            document.removeEventListener('click', handleElementClick);
            clearHighlight();
            closeEditor();
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
    
    function handleElementClick(e) {
        if (!isEditMode || !currentHighlighted) return;
        if (e.target === editIcon || currentEditor) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        openEditor(currentHighlighted);
    }
    
    function isPlainText(element) {
        const htmlContent = element.innerHTML.trim();
        const textContent = element.textContent.trim();
        return htmlContent === textContent && !/<[^>]*>/.test(htmlContent);
    }
    
    function openEditor(element) {
        closeEditor();
        
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        const isPlainTextContent = isPlainText(element);
        
        if (isPlainTextContent) {
            const computedStyle = window.getComputedStyle(element);
            
            currentEditor = document.createElement('textarea');
            currentEditor.value = element.textContent;
            
            currentEditor.style.cssText = `
                position: absolute;
                top: ${rect.top + scrollTop}px;
                left: ${rect.left + scrollLeft}px;
                width: ${rect.width}px;
                height: ${rect.height}px;
                font-family: ${computedStyle.fontFamily};
                font-size: ${computedStyle.fontSize};
                font-weight: ${computedStyle.fontWeight};
                font-style: ${computedStyle.fontStyle};
                line-height: ${computedStyle.lineHeight};
                color: ${computedStyle.color};
                background: transparent;
                border: 3px solid #007bff;
                border-radius: 4px;
                z-index: 9999;
                resize: none;
                outline: none;
                padding: ${computedStyle.paddingTop} ${computedStyle.paddingRight} ${computedStyle.paddingBottom} ${computedStyle.paddingLeft};
                margin: 0;
                box-sizing: border-box;
                text-align: ${computedStyle.textAlign};
                text-decoration: ${computedStyle.textDecoration};
                letter-spacing: ${computedStyle.letterSpacing};
                word-spacing: ${computedStyle.wordSpacing};
                text-transform: ${computedStyle.textTransform};
                overflow: hidden;
            `;
        } else {
            currentEditor = document.createElement('textarea');
            currentEditor.value = element.innerHTML;
            currentEditor.style.cssText = `
                position: absolute;
                top: ${rect.top + scrollTop}px;
                left: ${rect.left + scrollLeft}px;
                width: ${rect.width}px;
                height: ${rect.height}px;
                font-family: 'Courier New', Consolas, monospace;
                font-size: 12px;
                border: 3px solid #007bff;
                border-radius: 4px;
                background: #fff;
                z-index: 9999;
                resize: none;
                outline: none;
                padding: 8px;
                box-sizing: border-box;
            `;
        }
        
        const targetElement = element;
        
        currentEditor.addEventListener('blur', function() {
            if (isPlainTextContent) {
                targetElement.textContent = currentEditor.value;
            } else {
                targetElement.innerHTML = currentEditor.value;
            }
            closeEditor();
        });
        
        currentEditor.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeEditor();
            } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                if (isPlainTextContent) {
                    targetElement.textContent = currentEditor.value;
                } else {
                    targetElement.innerHTML = currentEditor.value;
                }
                closeEditor();
            }
        });
        
        document.body.appendChild(currentEditor);
        currentEditor.focus();
        currentEditor.select();
    }
    
    function closeEditor() {
        if (currentEditor) {
            document.body.removeChild(currentEditor);
            currentEditor = null;
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createEditIcon);
    } else {
        createEditIcon();
    }
})();