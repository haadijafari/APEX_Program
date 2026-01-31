import os
import shutil

# Define what to copy: (Source inside node_modules, Destination inside static)
files = [
    # Bootstrap CSS and JS
    (
        "node_modules/bootstrap/dist/css/bootstrap.min.css",
        "backend/static/vendor/bootstrap/css/bootstrap.min.css",
    ),
    (
        "node_modules/bootstrap/dist/css/bootstrap.min.css.map",
        "backend/static/vendor/bootstrap/css/bootstrap.min.css.map",
    ),
    (
        "node_modules/bootstrap/dist/js/bootstrap.bundle.min.js",
        "backend/static/vendor/bootstrap/js/bootstrap.bundle.min.js",
    ),
    (
        "node_modules/bootstrap/dist/js/bootstrap.bundle.min.js.map",
        "backend/static/vendor/bootstrap/js/bootstrap.bundle.min.js.map",
    ),
    # Bootstrap Icons
    (
        "node_modules/bootstrap-icons/font/bootstrap-icons.min.css",
        "backend/static/vendor/bootstrap-icons/bootstrap-icons.min.css",
    ),
    (
        "node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff",
        "backend/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff",
    ),
    (
        "node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2",
        "backend/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
    ),
    # Chart.js
    (
        "node_modules/chart.js/dist/chart.umd.min.js",
        "backend/static/vendor/chartjs/js/chart.umd.min.js",
    ),
    (
        "node_modules/chart.js/dist/chart.umd.min.js.map",
        "backend/static/vendor/chartjs/js/chart.umd.min.js.map",
    ),
    # Emoji Picker Element
    (
        "node_modules/emoji-picker-element/index.js",
        "backend/static/vendor/emoji-picker/index.js",
    ),
    (
        "node_modules/emoji-picker-element/picker.js",
        "backend/static/vendor/emoji-picker/picker.js",
    ),
    (
        "node_modules/emoji-picker-element/picker.js.map",
        "backend/static/vendor/emoji-picker/picker.js.map",
    ),
    (
        "node_modules/emoji-picker-element/database.js",
        "backend/static/vendor/emoji-picker/database.js",
    ),
    (
        "node_modules/emoji-picker-element/database.js.map",
        "backend/static/vendor/emoji-picker/database.js.map",
    ),
    (
        "node_modules/emoji-picker-element-data/en/emojibase/data.json",
        "backend/static/vendor/emoji-picker/data.json",
    ),
]

for src, dest in files:
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # Copy file
    shutil.copyfile(src, dest)
    print(f"✅ Updated: {dest}")

print("🎉 Vendor files updated successfully!")
