#!/usr/bin/env python3

import os
import json
from pathlib import Path
from urllib.parse import quote

def find_html_files(base_dir):
    """Find all HTML files in the ui_examples_new directory"""
    html_files = []
    base_path = Path(base_dir)
    
    for html_file in base_path.glob('**/*.html'):
        # Get relative path from base directory
        rel_path = html_file.relative_to(base_path)
        html_files.append(str(rel_path))
    
    return sorted(html_files)

def get_page_title(html_path, base_dir):
    """Generate a readable title for the HTML page"""
    # Remove .html extension and convert path to readable title
    title = html_path.replace('.html', '')
    
    # Replace slashes and underscores with spaces, capitalize words
    title = title.replace('/', ' > ').replace('_', ' ')
    title = ' '.join(word.capitalize() for word in title.split())
    
    return title

def generate_index_html(base_dir):
    """Generate the HTML index page"""
    html_files = find_html_files(base_dir)
    
    if not html_files:
        print("No HTML files found!")
        return
    
    # Start with the first file
    first_file = html_files[0] if html_files else ""
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Examples Index</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .sidebar-item:hover {{
            background-color: #f3f4f6;
        }}
        .sidebar-item.active {{
            background-color: #dbeafe;
            border-left: 4px solid #3b82f6;
        }}
    </style>
</head>
<body class="bg-gray-100 h-screen overflow-hidden">
    <div class="flex h-full">
        <!-- Sidebar -->
        <div class="w-80 bg-white shadow-lg overflow-y-auto">
            <div class="p-6 bg-blue-600 text-white">
                <h1 class="text-xl font-bold">UI Examples</h1>
                <p class="text-sm text-blue-100 mt-1">{len(html_files)} pages</p>
            </div>
            
            <div class="p-4">
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="Search pages..." 
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
            </div>
            
            <nav class="pb-6">
'''
    
    # Group files by category (first part of path)
    categories = {}
    for file_path in html_files:
        parts = file_path.split('/')
        if len(parts) > 1:
            category = parts[1]  # Skip 'templates'
        else:
            category = 'Root'
        
        if category not in categories:
            categories[category] = []
        categories[category].append(file_path)
    
    # Generate navigation
    for category, files in categories.items():
        html_content += f'''
                <div class="mb-4">
                    <h3 class="px-4 py-2 text-sm font-semibold text-gray-600 uppercase tracking-wider">{category.replace('_', ' ').replace('.html', '').title()}</h3>
'''
        
        for file_path in files:
            title = get_page_title(file_path, base_dir)
            # Remove the category part from title to avoid redundancy
            if ' > ' in title:
                title = ' > '.join(title.split(' > ')[2:])  # Skip 'Templates' and category
            
            # Use the full relative path from the web root
            full_path = f"ui_examples_new/{file_path}"
            encoded_path = quote(full_path)
            
            html_content += f'''
                    <a href="#" 
                       onclick="loadPage('{encoded_path}')" 
                       class="sidebar-item block px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors duration-200 border-l-4 border-transparent"
                       data-path="{file_path.lower()}"
                       data-title="{title.lower()}">
                        <div class="font-medium">{title}</div>
                        <div class="text-xs text-gray-500 mt-1">{file_path}</div>
                    </a>
'''
        
        html_content += '                </div>'
    
    html_content += '''
            </nav>
        </div>
        
        <!-- Main content area -->
        <div class="flex-1 flex flex-col">
            <header class="bg-white shadow-sm border-b px-6 py-4">
                <h2 id="currentPageTitle" class="text-xl font-semibold text-gray-800">Select a page to preview</h2>
                <p id="currentPagePath" class="text-sm text-gray-500 mt-1"></p>
            </header>
            
            <main class="flex-1 p-6">
                <div class="h-full bg-white rounded-lg shadow-sm border">
                    <iframe 
                        id="previewFrame" 
                        src="" 
                        class="w-full h-full rounded-lg"
                        frameborder="0">
                    </iframe>
                </div>
            </main>
        </div>
    </div>
    
    <script>
        function loadPage(encodedPath) {
            const path = decodeURIComponent(encodedPath);
            const iframe = document.getElementById('previewFrame');
            const titleElement = document.getElementById('currentPageTitle');
            const pathElement = document.getElementById('currentPagePath');
            
            // Update iframe source
            iframe.src = path;
            
            // Update header
            const title = getPageTitle(path);
            titleElement.textContent = title;
            pathElement.textContent = path;
            
            // Update active state
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const activeItem = document.querySelector(`[onclick="loadPage('${encodedPath}')"]`);
            if (activeItem) {
                activeItem.classList.add('active');
            }
        }
        
        function getPageTitle(path) {
            return path.replace('.html', '').replace(/\//g, ' > ').replace(/_/g, ' ')
                .split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        }
        
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const items = document.querySelectorAll('.sidebar-item');
            
            items.forEach(item => {
                const path = item.getAttribute('data-path') || '';
                const title = item.getAttribute('data-title') || '';
                const shouldShow = path.includes(searchTerm) || title.includes(searchTerm);
                
                if (shouldShow) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
        
        // Load first page by default
        window.addEventListener('load', function() {'''
    
    if html_files:
        first_full_path = f"ui_examples_new/{html_files[0]}"
        first_encoded = quote(first_full_path)
        html_content += f'''
            loadPage('{first_encoded}');'''
    
    html_content += '''
        });
    </script>
</body>
</html>'''
    
    return html_content

def main():
    base_dir = './ui_examples_new'
    
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found!")
        return
    
    print("Generating HTML index page...")
    html_content = generate_index_html(base_dir)
    
    output_file = 'ui_examples_index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Generated {output_file}")
    print(f"📁 Found {len(find_html_files(base_dir))} HTML pages")
    print(f"🌐 Open {output_file} in your browser to view the index")

if __name__ == "__main__":
    main()