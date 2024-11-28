# ROS Robot Tutorials
- [Build](#building-app)
- [Run](#running-app)
- [Packages list](#packages-list)

## Building App
1. First, clone repo to `your-project-folder/src` (IT`S NECESSARY TO CLONE INTO SRC FOLDER!)
2. Make sure you\`ve installed all `ros` dependencies with
```bash
cd ../ # if you was in src folder
rosdep install -i --from-path src --rosdistro iron -y
```
After installing, you will see `#All required rosdeps installed successfully` in terminal.
3. Move to your project\`s root dir and run:
```bash
colcon build
```
Or if you want to build only one package:
```bash
colcon build --packages-select package-name
```
3. Done!

## Running App
1. Make sure you\`ve done all steps in [Building App](#building-app)
2. Move to your project\`s root folder and run:
```bash
source install/setup.bash
```
3. Run module with:
```bash
ros2 run module-name entrypoint
```
The default package entypoint is `main` (it\`s always must be set)
See packages list [below](#packages-list)

## Packages List
Currently living packages:
1. main - main robot package (Python)
2. sensors - sensors host package (Python)
3. interfaces - client-server interfaces package (C++). Don\`t run it! It\`s for importing in other packages.
