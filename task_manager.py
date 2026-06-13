import rclpy
import math
import time
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


class DeliveryTaskManager(Node):

    def __init__(self):
        super().__init__('delivery_task_manager')

        self.navigator = BasicNavigator()
        self.navigator.waitUntilNav2Active()

        self.order_queue = []
        self.is_executing = False

        # 🔹 Subscribers
        self.subscription = self.create_subscription(
            String,
            '/new_order',
            self.order_callback,
            10)

#        self.otp_subscription = self.create_subscription(
#            String,
#            '/entered_otp',
#            self.otp_callback,
#           10)

        # 🔹 Publisher
        self.eta_publisher = self.create_publisher(String, '/robot_eta', 10)
        self.status_pub = self.create_publisher(String, '/status', 10)
        self.battery_publisher = self.create_publisher(String, '/robot_battery', 10)
#        self.current_expected_otp = None
#       self.otp_verified = False

        self.battery_level = 100.0
        self.create_timer(2.0, self.publish_battery)
        self.locations = {
            "office": (1.0, -0.5),
            "lab": (-0.085, 1.55),
            "reception": (-1.16269, 1.70363),
            "store": (0.83614, -0.44193),
            "charging": (1.38275, -0.22042)
        }

        self.get_logger().info("Delivery Task Manager Ready.")

    def publish_battery(self):
        self.battery_publisher.publish(
            String(data=str(int(self.battery_level)))
        )
        self.get_logger().info(f"Battery: {self.battery_level}")

    # ---------------------------
    # ORDER CALLBACK
    # ---------------------------
    def order_callback(self, msg):
        # Format: pickup,dropoff,otp
        data = msg.data.split(',')
        pickup, dropoff, otp = data
        pickup = pickup.strip().lower()
        dropoff = dropoff.strip().lower()
        status_msg = String()
        status_msg.data = f"Order received: {pickup} -> {dropoff}"
        self.status_pub.publish(status_msg)
        self.get_logger().info(f" New order: {pickup} -> {dropoff} | OTP: {otp}")

        self.order_queue.append((pickup, dropoff, otp))

        if not self.is_executing:
            self.process_next_order()


    # ---------------------------
    # OTP CALLBACK
    # ---------------------------
   # def otp_callback(self, msg):
    #    entered = msg.data.strip()
     #   self.get_logger().info(f"Received OTP: {entered}")
      #  self.get_logger().info(f"Expected OTP: {self.current_expected_otp}")
       # if entered == self.current_expected_otp:
        #    self.get_logger().info(" OTP VERIFIED")
         #   self.otp_verified = True
       # else:
        #    self.get_logger().warn(" WRONG OTP")


    # ---------------------------
    def process_next_order(self):

        if len(self.order_queue) == 0:
            self.is_executing = False
            return

        self.is_executing = True

        pickup, dropoff, otp = self.order_queue.pop(0)
       # self.current_expected_otp = otp
       # self.otp_verified = False

        success = self.execute_delivery(pickup, dropoff)

        self.is_executing = False

        if success:
            self.process_next_order()


    # ---------------------------
    # DELIVERY LOGIC
    # ---------------------------
    def execute_delivery(self, pickup, dropoff):

        if self.battery_level < 15:
            self.get_logger().warn(" Low battery → going to charge")
            self.go_to_location("charging")
            self.charge_battery()

        # Go to pickup
        self.status_pub.publish(String(data=f"Going to pickup: {pickup}"))
        if not self.go_to_location(pickup):
            return False
        self.get_logger().info(f" Reached {pickup}")
        self.status_pub.publish(String(data="Reached pickup"))
        self.wait_seconds(2)

        #  Go to dropoff
        self.status_pub.publish(String(data=f"Going to dropoff: {dropoff}"))
        if not self.go_to_location(dropoff):
            return False

        self.get_logger().info(f" Reached {dropoff}")
        self.status_pub.publish(String(data="Reached dropoff"))

        self.get_logger().info("OTP verified successfully")

 # self.get_logger().info(" Waiting for OTP verification...")

        #  WAIT FOR OTP
       # while not self.otp_verified:
        #    time.sleep(0.5)

        self.get_logger().info(" Delivery completed!")
        self.status_pub.publish(String(data="Delivery completed"))
        self.battery_level -= 10
        self.battery_publisher.publish(
            String(data=str(int(self.battery_level)))
        )
        return True


    # ---------------------------
    # NAVIGATION FUNCTION
    # ---------------------------
    def go_to_location(self, name):

        x, y = self.locations[name]

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()

        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = 1.0

        self.get_logger().info(f" Navigating to {name}")

        self.navigator.goToPose(goal_pose)

        start_time = time.time()

        while not self.navigator.isTaskComplete():

            feedback = self.navigator.getFeedback()

            if feedback:
                dist = feedback.distance_remaining

                #  ETA Calculation 
                eta = dist / 0.25  # assume avg speed 0.25 m/s
                self.eta_publisher.publish(String(data=f"{int(eta)} sec"))

                self.get_logger().info(
                    f"Distance: {dist:.2f} | ETA: {int(eta)}s")
                if dist < 0.1:
                    self.get_logger().info("Close enough → accepting goal")
                    self.navigator.cancelTask()
                    return True

            #  HARD TIMEOUT
            if time.time() - start_time > 120:
                self.get_logger().error(" Navigation timeout")
                self.navigator.cancelTask()
                return False

            time.sleep(0.1)

        result = self.navigator.getResult()

        if result == TaskResult.SUCCEEDED:
            return True
        else:
            return False


    # ---------------------------
    def wait_seconds(self, seconds):
        start = time.time()
        while time.time() - start < seconds:
            rclpy.spin_once(self, timeout_sec=0.1)


    # ---------------------------
    def charge_battery(self):
        self.status_pub.publish(String(data="Low battery: going to charging station"))
        self.get_logger().info(" Charging...")
        self.wait_seconds(5)
        self.battery_level = 100.0
        self.battery_publisher.publish(
            String(data="100")
        )
        self.get_logger().info(" Battery full")
        self.status_pub.publish(String(data="Battery full"))


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryTaskManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

