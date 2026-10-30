[app]

# (str) Title of your application
title = Mi Aplicacion

# (str) Package name
package.name = miapli

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (list) Source files to include (let it blank to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

# (int) Target Android API, should be one of the supported API levels
android.api = 33

# (int) Minimum API required
android.min_api = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True
