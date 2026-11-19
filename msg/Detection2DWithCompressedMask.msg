std_msgs/Header header
uint32 instance_id
string class_id
vision_msgs/BoundingBox2D bbox
vision_msgs/ObjectHypothesisWithPose hypothesis
# Full-size, lossless indexed PNG: bit depth 1, palette 0=background, 1=foreground.
# The palette expands to black (0) and white (255) when decoded as mono8.
sensor_msgs/CompressedImage mask
