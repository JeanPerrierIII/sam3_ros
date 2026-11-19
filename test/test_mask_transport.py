"""Verify the PNG wire format, lossless decoding, and detection integration."""

from io import BytesIO
import struct
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
from cv_bridge import CvBridge
import numpy as np
from PIL import Image
import pytest
from rclpy.serialization import deserialize_message, serialize_message
from std_msgs.msg import Header

from sam3_ros.msg import Detection2DWithCompressedMaskArray
from sam3_ros_node.mask_transport import encode_mask
from sam3_ros_node.sam3_node import Sam3Node


@pytest.mark.parametrize('shape', [(1, 1), (3, 7), (5, 8), (9, 17), (480, 640)])
@pytest.mark.parametrize('pattern', ['empty', 'full', 'random', 'noncontiguous'])
def test_png_format_and_round_trip(shape, pattern):
    """Keep odd-width rows, binary values, dimensions, and camera headers intact."""
    height, width = shape
    rng = np.random.default_rng(123)
    if pattern == 'empty':
        mask = np.zeros(shape, dtype=bool)
    elif pattern == 'full':
        mask = np.ones(shape, dtype=bool)
    elif pattern == 'noncontiguous':
        mask = rng.integers(0, 2, (height, width * 2), dtype=np.uint8)[:, ::2]
    else:
        mask = rng.integers(0, 2, shape, dtype=np.uint8) * 255
    header = Header(frame_id='camera_optical_frame')
    header.stamp.sec = 123
    header.stamp.nanosec = 456

    message = encode_mask(mask, header)
    payload = bytes(message.data)
    assert message.header == header
    assert message.format == 'mono8; png compressed'
    assert payload[:8] == b'\x89PNG\r\n\x1a\n'
    assert payload[12:16] == b'IHDR'
    # PNG IHDR: width, height, bit depth, color type. Type 3 is indexed color.
    assert struct.unpack('>IIBB', payload[16:26]) == (width, height, 1, 3)
    palette_offset = payload.index(b'PLTE')
    assert struct.unpack('>I', payload[palette_offset - 4:palette_offset])[0] == 6
    assert payload[palette_offset + 4:palette_offset + 10] == b'\0\0\0\xff\xff\xff'
    with Image.open(BytesIO(payload)) as image:
        assert image.mode == 'P'
        assert image.getpalette()[:6] == [0, 0, 0, 255, 255, 255]
        np.testing.assert_array_equal(np.asarray(image), mask.astype(bool))
    expected = mask.astype(bool).astype(np.uint8) * 255
    decoded = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_GRAYSCALE)
    np.testing.assert_array_equal(decoded, expected)
    np.testing.assert_array_equal(
        CvBridge().compressed_imgmsg_to_cv2(message, 'mono8'), expected)


def test_mask_payload_size():
    """Compress a representative 720p object far below raw mono8 transport."""
    mask = np.zeros((720, 1280), dtype=bool)
    mask[125:625, 400:800] = True
    payload = encode_mask(mask, Header()).data
    assert len(payload) < mask.size // 100


def test_detection_callback_and_ros_serialization():
    """Publish overlapping instances as compressed messages without inference."""
    first = np.zeros((19, 33), dtype=bool)
    first[2:10, 3:16] = True
    second = np.zeros_like(first)
    second[5:17, 9:28] = True
    empty = np.zeros_like(first)

    def tensor(mask):
        return SimpleNamespace(cpu=lambda: SimpleNamespace(numpy=lambda: mask))

    predictor = Mock(return_value=[SimpleNamespace(masks=SimpleNamespace(
        data=[tensor(first), tensor(empty), tensor(second)]))])
    bridge = CvBridge()
    node = SimpleNamespace(
        enable=True, bridge=bridge, last_stamp=None, predictor=predictor,
        prompt_text=['object'], get_color_for_class=lambda name: (0, 255, 0),
        pub_det_mask=Mock(), pub_det=Mock(), pub_img=Mock())
    image = bridge.cv2_to_imgmsg(np.zeros((19, 33, 3), dtype=np.uint8), 'bgr8')
    image.header = Header(frame_id='camera')
    image.header.stamp.sec = 42

    Sam3Node.image_cb(node, image)

    array = node.pub_det_mask.publish.call_args.args[0]
    wire = serialize_message(array)
    received = deserialize_message(wire, Detection2DWithCompressedMaskArray)
    assert received.header == image.header
    assert len(received.detections) == 2
    boxes = node.pub_det.publish.call_args.args[0].detections
    for index, mask in enumerate((first, second)):
        detection = received.detections[index]
        assert detection.header == image.header
        assert detection.instance_id == index
        assert detection.class_id == 'object'
        assert detection.hypothesis.hypothesis.class_id == 'object'
        assert detection.mask.header == image.header
        assert detection.bbox == boxes[index].bbox
        ys, xs = np.where(mask)
        assert detection.bbox.size_x == xs.max() - xs.min() + 1
        assert detection.bbox.size_y == ys.max() - ys.min() + 1
        np.testing.assert_array_equal(
            bridge.compressed_imgmsg_to_cv2(detection.mask, 'mono8'),
            mask.astype(np.uint8) * 255)

    # An empty inference still publishes an empty array with the frame header.
    predictor.return_value = []
    Sam3Node.image_cb(node, image)
    assert node.pub_det_mask.publish.call_args.args[0].detections == []
    assert node.pub_det_mask.publish.call_args.args[0].header == image.header
