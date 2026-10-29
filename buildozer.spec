[app]
title = J.A.R.V.I.S. Tactico
package.name = jarvistactico
package.domain = org.jarvis
source.include_exts = py,png,jpg,kv,atlas
source.dir = .
version = 0.1
requirements = python3,kivy,pyjnius
android.permissions = INTERNET, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, CAMERA, CALL_PHONE, ACCESS_NETWORK_STATE, WAKE_LOCK
orientation = portrait
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a