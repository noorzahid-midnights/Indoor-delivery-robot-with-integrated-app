# Indoor Delivery Robot

This project is an autonomous indoor delivery robot designed for indoor environments like offices, hospitals, warehouses, etc. It performs navigation, delivery, and user interaction through a mobile application.

## Features

- Autonomous navigation using SLAM
- Indoor mapping and localization
- Path planning and obstacle avoidance
- Battery monitoring
- Estimated Time of Arrival (ETA)
- OTP-based secure delivery
- Mobile app for order placement and tracking

## Tech Stack

### Robot Side
- ROS2
- Gazebo
- Python
- SLAM

### Mobile App
- Flutter
- Firebase (Authentication, Firestore)

## Project Structure

Indoor-Delivery-Robot/
- robot_simulation/
- navigation/
- mobile_app/
- backend/

## Workflow

1. User places an order through the mobile app
2. Robot receives the delivery request
3. Robot navigates using a pre-built SLAM map
4. Robot reaches destination
5. OTP verification is used to complete delivery

## Future Improvements

- Multi-robot coordination
- Real-time dynamic obstacle handling
- Integration with IoT devices
