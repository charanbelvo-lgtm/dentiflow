import os

js_dir = r"c:\Users\chara\OneDrive\Desktop\Dental\static\js"
os.makedirs(js_dir, exist_ok=True)

js_files = [
    'queue.js', 'treatment_plans.js', 'billing.js', 'inventory.js',
    'staff.js', 'reports.js', 'operations.js', 'booking.js',
    'branches.js', 'settings.js'
]

content = """document.addEventListener('DOMContentLoaded', () => {
    console.log('Module loaded.');
    // TODO: Fetch data and render UI
});
"""

for js_file in js_files:
    path = os.path.join(js_dir, js_file)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content.replace('Module', js_file))

print("JS files created successfully.")

