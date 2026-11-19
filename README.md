<a name="readme-top"></a>

[EN](README.md) | [JA](README_ja.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# SAM3 ROS

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#overview">Overview</a>
    </li>
    <li>
      <a href="#setup">Setup</a>
      <ul>
        <li><a href="#environment">Environment</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#download-sam-3-weight-file">Download SAM 3 Weight File</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#parameters">Parameters</a></li>
    <li><a href="#demo">Demo</a></li>
     <!-- <li><a href="#milestone">Milestone</a></li> -->
    <li><a href="#references">References</a></li>
  </ol>
</details>

## Overview
`sam3_ros` is a wrapper package that enables the use of Meta’s Segment Anything Model 3 (SAM3) in ROS 2.

This package performs **promptable segmentation using text prompts**, providing the following features in a ROS 2 environment.

**Main Features:**
- Object segmentation via text instructions  
- Multi-class and multi-instance support  
- Bounding box output (Detection2D)  
- Detection with lossless 1-bit indexed PNG masks (Detection2DWithCompressedMask)
- Visualization image output 

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Setup
This section explains how to set up this repository.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Environment

| System  | Version |
| ------------- | ------------- |
| Ubuntu | 22.04 (Jammy Jellyfish) |
| ROS | Humble Hawksbill |
| Python | 3.0~ |

### Installation
1. Move to your ROS 2 `src` directory.
   ```sh
   cd　~/colcon_ws/src/
   ```
2. Clone this repository.
   ```sh
   git clone -b humble-devel https://github.com/TeamSOBITS/sam3_ros.git
   ```
3. Navigate to this repository.
   ```sh
   cd sam3_ros
   ```
4. Install dependencies.
    ```sh
    bash install.sh
    ```
5. Build the package.
   ```sh
   cd ~/colcon_ws/
   colcon build --symlink-install
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Download SAM 3 Weight File
Due to licensing restrictions, the SAM 3 weight file (`sam3.pt`) is not downloaded automatically.
Therefore, you must **download it manually** in advance.

1. Visit the [**SAM 3 model page**](https://huggingface.co/facebook/sam3) on Hugging Face and request access to the model weights.

2. After approval, download [`sam3.pt`](https://huggingface.co/facebook/sam3/resolve/main/sam3.pt?download=true).

3. Place the downloaded `sam3.pt` file into the directory below.
   - Weight directory: （[`sam3_ros/weights`](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/weights)）

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Usage
1. Launch your camera and modify **image_topic_name** in [sam3.launch.py](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/launch/sam3.launch.py) to match your camera topic.
   
   Example:
   ```sh
   default_value="/camera/color/image_raw"              # orbbec_series
   ```
2. If using an RGB-D camera, also modify **point_cloud_topic** in [sam3.launch.py](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/launch/sam3.launch.py).
   Example:
   ```sh
   default_value="/camera/depth_registered/points"     # orbbec_series
   ```
3. Place your prepared weight file into the [weights directory](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/weights).
4. Update **weight_file** in [sam3.launch.py](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/launch/sam3.launch.py)
   ```sh
   default_value=os.path.join(get_package_share_directory("sam3_ros"), "weights", "sam3.pt")
   ```
5. Rebuild the package.
   ```sh
   cd ~/colcon_ws/
   colcon build --symlink-install
   ```
6. Launch SAM 3.
    ```sh
    ros2 launch sam3_ros sam3.launch.py
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Parameters
The following parameters can be configured in [sam3.launch.py](https://github.com/TeamSOBITS/sam3_ros/blob/humble-devel/launch/sam3.launch.py).


| Parameter               | Description                                                                                                                     | Default    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| weight_file             | SAM3 weight file                                                                                                                | sam3.pt    |
| prompt_text             | Target segmentation classes (string array)                                                                                      | ["object"] |
| threshold               | Mask confidence threshold                                                                                                       | 0.75       |
| half                    | Enable FP16 inference                                                                                                           | True       |
| image_show              | Enable Ultralytics visualization                                                                                                | False      |
| execute_default         | Enable inference on startup                                                                                                     | True       |
| use_3d                  | Enable 3D detection                                                                                                             | False      |
| cluster_tolerance       | Distance threshold for grouping point clouds into a single object. Larger values increase search range and slow processing.     | 0.01       |
| min_clusterSize         | Minimum number of points to be considered a valid object (smaller clusters are treated as noise).                               | 100        |
| max_clusterSize         | Maximum number of points allowed for one object (larger clusters are rejected as background, e.g., floor).                      | 20000      |
| noise_point_cloud_range | Amount of point cloud trimming in x/y/z to remove background surfaces (floor/walls). Excessive values may remove object points. | 0.01       |
| fast_shot               | Enable fast_shot                                                                                                                | true       |
| enable_id               | Append IDs to detected labels (e.g., apple_01)                                                                                  | false      |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Publications

| Topic                                   | Type                     | Description                  |
| --------------------------------------- | ------------------------ | ---------------------------- |
| `/sam3_ros/object_boxes`                | Detection2DArray         | Bounding boxes only          |
| `/sam3_ros/object_detections_with_mask` | sam3_ros/Detection2DWithCompressedMaskArray | Detection results with 1-bit indexed PNG masks |
| `/sam3_ros/segmented_image`             | sensor_msgs/Image        | Visualization image          |

Each detection's `mask` is a `sensor_msgs/CompressedImage` with format
`mono8; png compressed`. Its data is a complete lossless PNG with bit depth 1
and indexed color (PNG color type 3). Palette index 0 is background (black),
and index 1 is foreground (white). Masks retain their original dimensions and
camera header, including overlapping instances. The pixels are packed eight
per byte before PNG compression at level 9.

**Subscriber migration:** the topic now uses the messages defined in this
package, replacing `sobits_interfaces/Detection2DWithMaskArray`. Rebuild and
source the workspace on publishers and subscribers, then update the import and
decode the compressed mask instead of calling `imgmsg_to_cv2`:

```python
from cv_bridge import CvBridge
from sam3_ros.msg import Detection2DWithCompressedMaskArray

bridge = CvBridge()

def detection_callback(message: Detection2DWithCompressedMaskArray):
    for detection in message.detections:
        mask_mono8 = bridge.compressed_imgmsg_to_cv2(detection.mask, 'mono8')
        mask_bool = mask_mono8 != 0
```

Pillow readers can access palette indices as 0/1 directly; converting to
grayscale returns 0/255. Bounding box and visualization topic types are unchanged.
This package now uses `ament_cmake` to generate its messages and install the Python
node; the launch command remains the same. Pillow is required (`python3-pil` via
rosdep, or installed by `install.sh`). The visualization topic still carries a raw
color image; subscribe to it only when needed on a bandwidth-limited connection.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Demo
| Object Detection | Object Recognition | Instance Segmentation |
|:---:|:---:|:---:|
| ![](docs/sam3_object_raw.png) | ![](docs/sam3_multiclass_raw.png) | ![](docs/sam3_instant_raw.png) |
| ![](docs/sam3_object_result.png) | ![](docs/sam3_multiclass_result.png) | ![](docs/sam3_instant_result.png) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## References
* [SAM 3: Segment Anything with Concepts](https://github.com/facebookresearch/sam3)
* [ Ultralytics Documentation](https://docs.ultralytics.com/models/sam-3/)

[contributors-shield]: https://img.shields.io/github/contributors/TeamSOBITS/sam3_ros.svg?style=for-the-badge
[contributors-url]: https://github.com/TeamSOBITS/sam3_ros/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TeamSOBITS/sam3_ros.svg?style=for-the-badge
[forks-url]: https://github.com/TeamSOBITS/sam3_ros/network/members
[stars-shield]: https://img.shields.io/github/stars/TeamSOBITS/sam3_ros.svg?style=for-the-badge
[stars-url]: https://github.com/TeamSOBITS/sam3_ros/stargazers
[issues-shield]: https://img.shields.io/github/issues/TeamSOBITS/sam3_ros.svg?style=for-the-badge
[issues-url]: https://github.com/TeamSOBITS/sam3_ros/issues
[license-shield]: https://img.shields.io/github/license/TeamSOBITS/sam3_ros.svg?style=for-the-badge
[license-url]: LICENSE
