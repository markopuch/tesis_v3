# tesis_v3

Install usb camera 

'''
sudo apt update
sudo apt install -y \
  ros-jazzy-usb-cam \
  ros-jazzy-image-transport \
  ros-jazzy-camera-info-manager \
  ros-jazzy-image-tools \
  ros-jazzy-rqt-image-view \
  v4l-utils
  '''

  ros2 pkg list | grep -E 'usb_cam|image_transport|camera_info_manager|image_tools|rqt_image_view'

  ros2 run usb_cam usb_cam_node_exe
  ros2 run rqt_image_view rqt_image_view

  check: 
  v4l2-ctl --list-devices

  camera logitech brio in laptop: 

  ros2 run usb_cam usb_cam_node_exe \
  --ros-args \
  -p video_device:=/dev/video4 \
  -p image_width:=640 \
  -p image_height:=480 \
  -p framerate:=30.0