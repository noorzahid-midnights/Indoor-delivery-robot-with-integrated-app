import math
import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import PoseWithCovarianceStamped

import firebase_admin
from firebase_admin import credentials, firestore


# ---------------- FIREBASE ----------------
cred = credentials.Certificate("/home/bhagad/ros2_ws/serviceAccountKey.json.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


class FirebaseListener(Node):

    def __init__(self):
        super().__init__('firebase_listener')

        self.robot_x = 0.0
        self.robot_y = 0.0

        # Pose subscriber 
        self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.pose_callback,
            10
        )

        # Battery subscriber 
        self.create_subscription(
            String,
            '/robot_battery',
            self.battery_callback,
            10
        )

        # Publisher to Task Manager
        self.order_pub = self.create_publisher(String, '/new_order', 10)

        # Timer
        self.timer = self.create_timer(2.0, self.check_orders)

        # Prevent duplicate orders
        self.last_order_id = None

        self.get_logger().info("Firebase Listener Started")

    # ---------------- POSE ----------------
    def pose_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    # ---------------- CHECK ORDERS ----------------
    def check_orders(self):

        docs = db.collection("orders").stream()

        for doc in docs:
            data = doc.to_dict()
            order_id = doc.id

            # Skip already processed order
            if order_id == self.last_order_id:
                continue

            if data.get("status") != "pending":
                continue

            pickup = data.get("pickup")
            dropoff = data.get("dropoff")
            otp = data.get("otp", "1234")

            if not pickup or not dropoff:
                continue

            # Create message for Task Manager
            msg = String()
            msg.data = f"{pickup.get('name','office')},{dropoff.get('name','lab')},{otp}"

            # Publish order
            self.order_pub.publish(msg)

            self.get_logger().info(f"Order Sent → {msg.data}")

            # Mark as accepted in Firebase
            db.collection("orders").document(order_id).update({
                "status": "accepted"
            })

            # Save last order
            self.last_order_id = order_id

            break

    # ---------------- BATTERY ----------------
    def battery_callback(self, msg):
        battery = msg.data

        db.collection("robot_status").document("current").set({
            "battery": battery
        }, merge=True)


def main():
    rclpy.init()
    node = FirebaseListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
