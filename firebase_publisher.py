import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import firebase_admin
from firebase_admin import credentials, firestore


cred = credentials.Certificate("/home/bhagad/ros2_ws/serviceAccountKey.json.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


class FirebasePublisher(Node):

    def __init__(self):
        super().__init__('firebase_publisher')

        # listen to status coming from Task Manager
        self.create_subscription(
            String,
            '/status',
            self.status_callback,
            10
        )

        # listen to battery
        self.create_subscription(
            String,
            '/robot_battery',
            self.battery_callback,
            10
        )
        self.create_subscription(
            String,
            '/robot_eta',
            self.eta_callback,
            10
        )
    def status_callback(self, msg):
        db.collection("delivery").document("status").set({
            "state": msg.data
        })

    def battery_callback(self, msg):
        db.collection("robot_status").document("current").set({
            "battery": msg.data
        }, merge=True)

    def eta_callback(self, msg):
        db.collection("robot_status").document("current").set({
            "eta": msg.data
        }, merge=True)
def main():
    rclpy.init()
    node = FirebasePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
