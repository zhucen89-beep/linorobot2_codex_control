#!/usr/bin/env python3
"""Expose Gazebo camera data in compact forms suitable for an MCP client.

The ROS-MCP server remains responsible for transporting these topics to Codex.
This node avoids sending full raw Image arrays when a JPEG preview is enough.
"""

import json
import math

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import String


class CodexPerceptionGateway(Node):
    def __init__(self):
        super().__init__('codex_perception_gateway')
        self.bridge = CvBridge()
        self.latest_color = None
        self.latest_depth = None
        self.latest_color_stamp = None
        self.latest_depth_stamp = None

        self.color_pub = self.create_publisher(
            CompressedImage, '/codex/perception/rgb/compressed', 1)
        self.depth_pub = self.create_publisher(
            CompressedImage, '/codex/perception/depth/compressed', 1)
        self.status_pub = self.create_publisher(
            String, '/codex/perception/status', 1)

        self.create_subscription(
            Image, '/camera/color/image_raw', self.color_callback, 10)
        self.create_subscription(
            Image, '/camera/depth/image_rect_raw', self.depth_callback, 10)
        self.create_timer(0.5, self.publish_status)

    def color_callback(self, msg):
        try:
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            ok, encoded = cv2.imencode(
                '.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not ok:
                raise RuntimeError('JPEG encoding failed')
            out = CompressedImage()
            out.header = msg.header
            out.format = 'jpeg'
            out.data = encoded.tobytes()
            self.color_pub.publish(out)
            self.latest_color = image
            self.latest_color_stamp = msg.header.stamp
        except Exception as exc:
            self.get_logger().warning(f'RGB conversion failed: {exc}')

    def depth_callback(self, msg):
        try:
            depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            depth = np.asarray(depth)
            depth_m = depth.astype(np.float32)
            if msg.encoding in ('16UC1', 'mono16'):
                depth_m *= 0.001
            depth_m[~np.isfinite(depth_m)] = 0.0
            self.latest_depth = depth_m
            self.latest_depth_stamp = msg.header.stamp

            valid = depth_m[(depth_m > 0.05) & (depth_m < 10.0)]
            if valid.size:
                preview = np.clip(depth_m / 5.0 * 255.0, 0, 255).astype(np.uint8)
                preview = cv2.applyColorMap(preview, cv2.COLORMAP_JET)
            else:
                preview = np.zeros((depth_m.shape[0], depth_m.shape[1], 3), dtype=np.uint8)
            ok, encoded = cv2.imencode(
                '.jpg', preview, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                raise RuntimeError('depth JPEG encoding failed')
            out = CompressedImage()
            out.header = msg.header
            out.format = 'jpeg; depth_scale=0.001m'
            out.data = encoded.tobytes()
            self.depth_pub.publish(out)
        except Exception as exc:
            self.get_logger().warning(f'depth conversion failed: {exc}')

    def publish_status(self):
        status = {
            'rgb_available': self.latest_color is not None,
            'depth_available': self.latest_depth is not None,
            'rgb_topic': '/codex/perception/rgb/compressed',
            'depth_topic': '/codex/perception/depth/compressed',
            'depth_units': 'meters',
        }
        if self.latest_depth is not None:
            h, w = self.latest_depth.shape[:2]
            y0, y1 = max(0, h // 2 - 15), min(h, h // 2 + 15)
            x0, x1 = max(0, w // 2 - 15), min(w, w // 2 + 15)
            center = self.latest_depth[y0:y1, x0:x1]
            center = center[(center > 0.05) & (center < 10.0)]
            if center.size:
                status['center_depth_m'] = round(float(np.median(center)), 3)
        msg = String()
        msg.data = json.dumps(status, separators=(',', ':'))
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CodexPerceptionGateway()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
