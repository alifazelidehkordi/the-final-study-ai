[app]

title = The Final Study AI
project_dir = ..
input_file = gui/__main__.py
exec_directory = ../dist
project_file =
icon =

[python]

python_path =
packages = Nuitka==4.0

[qt]

qml_files =
excluded_qml_plugins =
modules = Core,Gui,Widgets
plugins = iconengines,imageformats,platforms,platformthemes,styles

[nuitka]

macos.permissions =
mode = standalone
extra_args = --quiet --assume-yes-for-downloads --noinclude-qt-translations --include-data-dir=gui/resources=gui/resources --include-data-dir=schemas=schemas

[android]

wheel_pyside =
wheel_shiboken =
plugins =

[buildozer]

mode = debug
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_libs =
arch =